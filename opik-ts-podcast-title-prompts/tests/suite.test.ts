import { describe, expect, it } from "vitest";
import { EPISODES } from "../src/episodes.js";
import { EXECUTION_POLICY, episodeFromItem, formatCopy } from "../src/suite.js";

describe("suite helpers", () => {
  it("formats copy the way the judge reads it", () => {
    expect(formatCopy({ title: "T", blurb: "B." })).toBe("Title: T\nBlurb: B.");
  });

  it("rebuilds an episode from a suite item that also carries an id", () => {
    const episode = EPISODES[1]!;
    expect(episodeFromItem({ id: "abc", ...episode })).toEqual(episode);
  });

  it("rejects an item that is not an episode", () => {
    expect(() => episodeFromItem({ id: "abc", show: "x" })).toThrow(/not an episode/);
  });

  it("requires a majority of runs to pass", () => {
    expect(EXECUTION_POLICY.passThreshold).toBeGreaterThan(EXECUTION_POLICY.runsPerItem / 2);
  });
});
