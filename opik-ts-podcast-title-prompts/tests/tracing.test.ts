import { describe, expect, it } from "vitest";
import { EPISODES } from "../src/episodes.js";
import { tracedCopywriter } from "../src/tracing.js";
import { stubClient } from "./helpers.js";

describe("tracedCopywriter with tracking disabled", () => {
  it("still returns the parsed copy and loads the prompt once per call", async () => {
    let loads = 0;
    const calls: unknown[] = [];
    const write = tracedCopywriter(stubClient("Title: T\nBlurb: B.", calls), async () => {
      loads += 1;
      return { name: "episode-title-blurb", prompt: "SYSTEM", version: "v2", commit: "abc12345" };
    });
    // OPIK_TRACK_DISABLE=true (set in vitest.config.ts) turns tracing into a no-op,
    // so the traced function behaves like the plain one.
    expect(await write(EPISODES[0]!)).toEqual({ title: "T", blurb: "B." });
    expect(loads).toBe(1);
    expect((calls[0] as { messages: { content: string }[] }).messages[0]?.content).toBe("SYSTEM");
  });
});
