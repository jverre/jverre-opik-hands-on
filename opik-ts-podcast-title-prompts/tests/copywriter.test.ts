import { describe, expect, it } from "vitest";
import { parseCopy, writeEpisodeCopy } from "../src/copywriter.js";
import { EPISODES } from "../src/episodes.js";
import { PROMPT_V2, formatEpisode } from "../src/prompts.js";
import { stubClient } from "./helpers.js";

describe("parseCopy", () => {
  it("reads the title and blurb lines", () => {
    expect(parseCopy("Title: Soup for 200\nBlurb: Ines Calloway feeds a snowed-in school.")).toEqual({
      title: "Soup for 200",
      blurb: "Ines Calloway feeds a snowed-in school.",
    });
  });

  it("keeps a multi-line blurb together", () => {
    const copy = parseCopy("Title: Long one\nBlurb: First sentence.\nSecond sentence.");
    expect(copy.blurb).toBe("First sentence.\nSecond sentence.");
  });

  it("throws when a line is missing", () => {
    expect(() => parseCopy("Title: Only a title")).toThrow(/missing a Title or Blurb/);
  });
});

describe("writeEpisodeCopy", () => {
  it("sends the prompt as system message and the episode facts as user message", async () => {
    const calls: unknown[] = [];
    const episode = EPISODES[0]!;
    const copy = await writeEpisodeCopy(stubClient("Title: T\nBlurb: B.", calls), PROMPT_V2, episode);
    expect(copy).toEqual({ title: "T", blurb: "B." });
    const request = calls[0] as { messages: { role: string; content: string }[] };
    expect(request.messages[0]).toEqual({ role: "system", content: PROMPT_V2 });
    expect(request.messages[1]?.content).toBe(formatEpisode(episode));
    expect(request.messages[1]?.content).toContain(episode.guest);
  });
});
