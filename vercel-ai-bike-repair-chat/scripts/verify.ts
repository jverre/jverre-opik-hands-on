// Read-back check: prints what the project holds in Opik (traces, span shape,
// usage and cost, threads, judge scores). Run it after `npm run demo`.
import path from "node:path";
import { fileURLToPath } from "node:url";
import { config } from "dotenv";
import { Opik } from "opik";
import { PROJECT_NAME, TRACE_NAME } from "../lib/telemetry";
import { RULE_NAME, SCORE_NAME } from "../lib/online-rule";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
config({ path: path.join(root, ".env"), quiet: true });
config({ path: path.join(root, "..", ".env"), quiet: true });

async function main() {
  const client = new Opik({ projectName: PROJECT_NAME });
  const api = client.api;

  const all = (await api.traces.getTracesByProject({ projectName: PROJECT_NAME, size: 100 })).content ?? [];
  // The online rule's own judge calls are logged in the project as `online_evaluation` traces.
  const traces = all.filter((t) => t.name === TRACE_NAME);
  console.log(`project ${PROJECT_NAME}: ${all.length} traces (${traces.length} chat turns, ${all.length - traces.length} judge calls)`);
  const threads = new Set(traces.map((t) => t.threadId).filter(Boolean));
  console.log(`threads: ${threads.size}`);

  const chatIds = new Set(traces.map((t) => t.id));
  const spans = ((await api.spans.getSpansByProject({ projectName: PROJECT_NAME, size: 200 })).content ?? []).filter((s) => chatIds.has(s.traceId ?? ""));
  const byType: Record<string, number> = {};
  for (const s of spans) byType[s.type ?? "?"] = (byType[s.type ?? "?"] ?? 0) + 1;
  console.log(`chat-turn spans: ${spans.length} ${JSON.stringify(byType)}`);

  for (const t of traces.slice().reverse()) {
    const own = spans.filter((s) => s.traceId === t.id);
    const score = t.feedbackScores?.find((s) => s.name === SCORE_NAME);
    console.log(
      `  ${t.name} thread=${String(t.threadId).slice(0, 8)} spans=${own.map((s) => `${s.type}:${s.name}`).join(",")} ` +
        `tokens=${JSON.stringify(t.usage ?? {})} cost=${t.totalEstimatedCost ?? "null"} ${SCORE_NAME}=${score?.value ?? "none"}`,
    );
  }

  const rules = await api.automationRuleEvaluators.findEvaluators({ name: RULE_NAME, size: 20 });
  console.log(`rules named ${RULE_NAME}: ${rules.content?.filter((r) => r.name === RULE_NAME).length ?? 0}`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
