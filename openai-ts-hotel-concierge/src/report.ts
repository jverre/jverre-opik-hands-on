import { PROJECT_NAME, flushTraces, getOpik } from "./tracing.js";

export interface TurnRow {
  thread: string;
  turn: number;
  tokens: number;
  cost: number | undefined;
  scores: string;
}

interface TraceLike {
  startTime: Date;
  threadId?: string;
  usage?: Record<string, number>;
  totalEstimatedCost?: number;
  feedbackScores?: { name: string; value: number }[];
}

/** Turn raw trace records into one row per guest message, ordered by thread then time. */
export function toTurnRows(traces: TraceLike[]): TurnRow[] {
  const sorted = [...traces].sort(
    (a, b) =>
      (a.threadId ?? "").localeCompare(b.threadId ?? "") ||
      a.startTime.getTime() - b.startTime.getTime(),
  );
  const counters = new Map<string, number>();
  return sorted.map((t) => {
    const thread = t.threadId ?? "(no thread)";
    const turn = (counters.get(thread) ?? 0) + 1;
    counters.set(thread, turn);
    return {
      thread,
      turn,
      tokens: t.usage?.total_tokens ?? 0,
      cost: t.totalEstimatedCost,
      scores: (t.feedbackScores ?? []).map((s) => `${s.name}=${s.value}`).join(", "),
    };
  });
}

export function formatRows(rows: TurnRow[]): string {
  const money = (c: number | undefined) => (c === undefined ? "n/a" : `$${c.toFixed(6)}`);
  const lines = rows.map(
    (r) =>
      `${r.thread.padEnd(34)} turn ${r.turn} ${String(r.tokens).padStart(6)} tokens ${money(r.cost).padStart(10)}  ${r.scores}`,
  );
  const total = rows.reduce((sum, r) => sum + (r.cost ?? 0), 0);
  return [...lines, `${"total".padEnd(34)}        ${"".padStart(13)} ${money(total).padStart(10)}`].join("\n");
}

/** Read the project back from Opik and print tokens, cost and scores per guest message. */
export async function printCostReport(expectedTraces: number): Promise<void> {
  await flushTraces();
  // searchTraces reads from the Opik backend; waitForAtLeast polls until the
  // flushed traces are queryable, because ingestion is asynchronous.
  const traces = await getOpik().searchTraces({
    projectName: PROJECT_NAME,
    waitForAtLeast: expectedTraces,
    waitForTimeout: 30,
  });
  console.log(`\nPer-turn usage read back from Opik (${PROJECT_NAME}):\n${formatRows(toTurnRows(traces))}`);
}
