// Scripted demo: sets up the online evaluation rule, starts the Next.js dev
// server on a private port, plays three rider conversations against /api/chat,
// waits for the judge scores to appear in Opik, and shuts the server down.
import { spawn } from "node:child_process";
import { randomUUID } from "node:crypto";
import { setTimeout as sleep } from "node:timers/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { config } from "dotenv";
import { Opik } from "opik";
import { ensureOnlineRule, RULE_NAME, SCORE_NAME } from "../lib/online-rule";
import { PROJECT_NAME, TRACE_NAME } from "../lib/telemetry";
import { conversations } from "./conversations";
import { readReply } from "./sse";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
config({ path: path.join(root, ".env"), quiet: true });
config({ path: path.join(root, "..", ".env"), quiet: true });

const PORT = process.env.DEMO_PORT || "4191";
const BASE = `http://localhost:${PORT}`;

if (!process.env.OPENAI_API_KEY) {
  console.error("Missing OPENAI_API_KEY. Copy .env.example to .env and fill it in.");
  process.exit(1);
}

// The client is used here only for setup and read-back; the server process has its own.
const client = new Opik({ projectName: PROJECT_NAME });

const message = (role: "user" | "assistant", text: string) => ({
  id: randomUUID(),
  role,
  parts: [{ type: "text", text }],
});

async function chatTurn(chatId: string, messages: unknown[]): Promise<string> {
  const res = await fetch(`${BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id: chatId, messages }),
  });
  if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
  return readReply(res.body, (delta) => process.stdout.write(delta));
}

async function waitForServer(timeoutMs = 90_000) {
  const deadline = Date.now() + timeoutMs;
  let lastError: unknown;
  while (Date.now() < deadline) {
    try {
      if ((await fetch(BASE, { signal: AbortSignal.timeout(3000) })).ok) return;
    } catch (error) {
      lastError = error;
    }
    await sleep(500);
  }
  throw new Error("Dev server did not become ready in time", { cause: lastError });
}

async function printJudgeScores(expectedTraces: number) {
  // The rule runs asynchronously on the Opik server, so poll for the scores.
  const deadline = Date.now() + 150_000;
  for (;;) {
    const page = await client.api.traces.getTracesByProject({ projectName: PROJECT_NAME, size: 50 });
    // The judge's own model calls are logged in the project too; look at chat turns only.
    const traces = (page.content ?? []).filter((t) => t.name === TRACE_NAME);
    const scored = traces.filter((t) => t.feedbackScores?.some((s) => s.name === SCORE_NAME));
    if (scored.length >= expectedTraces || Date.now() > deadline) {
      console.log(`\n${traces.length} traces, ${scored.length} scored by ${RULE_NAME}:`);
      for (const t of traces.slice().reverse()) {
        const score = t.feedbackScores?.find((s) => s.name === SCORE_NAME)?.value;
        console.log(`  thread ${String(t.threadId).slice(0, 8)}  ${SCORE_NAME}=${score ?? "pending"}`);
      }
      return;
    }
    await sleep(5000);
  }
}

async function main() {
  const rule = await ensureOnlineRule(client);
  console.log(`Online rule ${RULE_NAME}: ${rule.created ? "created" : "already present"}`);

  console.log(`Starting Next.js dev server on port ${PORT}...`);
  const next = spawn(path.join(root, "node_modules", ".bin", "next"), ["dev", "-p", PORT], {
    cwd: root,
    env: { ...process.env },
    stdio: ["ignore", "pipe", "pipe"],
    detached: true, // own process group, so the whole tree can be stopped
  });
  next.stdout.on("data", () => {});
  next.stderr.on("data", (d) => {
    if (/error/i.test(String(d))) process.stderr.write(String(d));
  });

  let turns = 0;
  try {
    await waitForServer();
    console.log("Server is ready.\n");

    for (const conversation of conversations) {
      const chatId = randomUUID();
      console.log(`=== ${conversation.title} (thread ${chatId.slice(0, 8)}) ===`);
      const history: ReturnType<typeof message>[] = [];
      for (const turn of conversation.turns) {
        console.log(`\nRider: ${turn}\nSpoke: `);
        history.push(message("user", turn));
        history.push(message("assistant", await chatTurn(chatId, history)));
        turns += 1;
        console.log();
      }
    }

    // The exporter queues spans in the server process; give it time to send them.
    console.log("Waiting for traces to reach Opik...");
    await sleep(8_000);
    await printJudgeScores(turns);
    console.log(`Done. Open the ${PROJECT_NAME} project in Opik.`);
  } finally {
    try {
      process.kill(-next.pid!, "SIGTERM");
    } catch {
      /* already gone */
    }
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
