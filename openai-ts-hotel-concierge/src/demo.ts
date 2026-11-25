import { createInterface } from "node:readline/promises";
import OpenAI from "openai";
import { Concierge } from "./concierge.js";
import { loadNearestEnv } from "./env.js";
import { printCostReport } from "./report.js";
import { PROJECT_NAME, flushTraces, getOpik } from "./tracing.js";

loadNearestEnv();

// Scripted guest conversations so the demo runs with no typing.
export const DEMO_CONVERSATIONS: Record<string, string[]> = {
  "room-412-late-checkout-and-spa": [
    "Hi, I'm in room 412. Can I get a late checkout tomorrow? I'm not a Gold member.",
    "Thanks, I will ask the front desk about the 16:00 one. Is there a massage slot free this afternoon?",
    "Perfect, and where should I eat tonight after that?",
  ],
  "room-208-towels-and-trip-ask": [
    "Could you send two extra towels to room 208?",
    "Thanks! While you're there, can you book me a flight to Lisbon on Friday?",
    "Fine. Then what time does the Lantern Bar open?",
  ],
};

// Simulated guest reactions, keyed by conversation: which turn gets rated and how.
const FEEDBACK: Record<string, { turn: number; value: number; reason: string }> = {
  "room-412-late-checkout-and-spa": { turn: 3, value: 1, reason: "Guest liked the dinner tip." },
  "room-208-towels-and-trip-ask": { turn: 2, value: 0, reason: "Guest wanted the flight booked, not a redirect." },
};

async function runDemo(client: OpenAI): Promise<number> {
  const rated: { id: string; name: string; value: number; reason: string }[] = [];
  let turns = 0;
  for (const [conversationId, userTurns] of Object.entries(DEMO_CONVERSATIONS)) {
    console.log(`\n=== Conversation: ${conversationId} ===`);
    const concierge = new Concierge(conversationId, client);
    for (const [index, userMessage] of userTurns.entries()) {
      console.log(`\nGuest:     ${userMessage}`);
      console.log(`Concierge: ${await concierge.answer(userMessage)}`);
      turns += 1;
      const fb = FEEDBACK[conversationId];
      if (fb && fb.turn === index + 1 && concierge.lastTraceId) {
        rated.push({ id: concierge.lastTraceId, name: "guest-satisfaction", value: fb.value, reason: fb.reason });
      }
    }
  }

  // After the run, attach the guest ratings to the traces they refer to. They show
  // up as a sortable guest-satisfaction column in the traces table. Flush first so
  // the traces exist server-side before scores are written to them.
  await flushTraces();
  getOpik().logTracesFeedbackScores(rated);
  console.log(`\nLogged guest-satisfaction on ${rated.length} traces.`);
  return turns;
}

async function runInteractive(client: OpenAI): Promise<void> {
  const concierge = new Concierge(`interactive-${Date.now().toString(36)}`, client);
  console.log(`Harbourlight concierge (conversation ${concierge.conversationId}). Ctrl+D to quit.`);
  const rl = createInterface({ input: process.stdin, output: process.stdout });
  try {
    for (;;) {
      const line = (await rl.question("\nYou: ")).trim();
      if (line) console.log(`Concierge: ${await concierge.answer(line)}`);
    }
  } catch {
    console.log("\nGoodbye!");
  } finally {
    rl.close();
  }
}

async function main(): Promise<void> {
  const client = new OpenAI();
  try {
    if (process.argv.includes("--interactive")) await runInteractive(client);
    else await printCostReport(await runDemo(client));
  } finally {
    // Flush before exit (even on errors) so the last turns reach Opik.
    await flushTraces();
  }
  console.log(`\nTraces sent to the "${PROJECT_NAME}" project in Opik.`);
}

main().catch((err) => {
  console.error(err);
  process.exitCode = 1;
});
