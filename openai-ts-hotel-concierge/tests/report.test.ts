import { describe, expect, it } from "vitest";
import { formatRows, toTurnRows } from "../src/report.js";

describe("cost report", () => {
  const traces = [
    { startTime: new Date(2026, 0, 1, 10, 0, 2), threadId: "b", usage: { total_tokens: 300 }, totalEstimatedCost: 0.0002 },
    { startTime: new Date(2026, 0, 1, 10, 0, 1), threadId: "b", usage: { total_tokens: 200 }, totalEstimatedCost: 0.0001 },
    {
      startTime: new Date(2026, 0, 1, 10, 0, 0),
      threadId: "a",
      usage: { total_tokens: 100 },
      feedbackScores: [{ name: "guest-satisfaction", value: 1 }],
    },
  ];

  it("numbers turns per thread in time order", () => {
    const rows = toTurnRows(traces);
    expect(rows.map((r) => `${r.thread}:${r.turn}:${r.tokens}`)).toEqual(["a:1:100", "b:1:200", "b:2:300"]);
    expect(rows[0]?.scores).toBe("guest-satisfaction=1");
  });

  it("prints n/a when cost is missing and sums the rest", () => {
    const text = formatRows(toTurnRows(traces));
    expect(text).toContain("n/a");
    expect(text).toContain("$0.000300");
  });
});
