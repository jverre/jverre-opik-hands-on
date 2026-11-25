import path from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import { formatPassages, loadCorpus, parseGame, retrieve, tokenize } from "../src/rules.js";

const corpus = loadCorpus(path.join(path.dirname(fileURLToPath(import.meta.url)), "../data/rules"));

describe("rules corpus", () => {
  it("splits a game into one passage per section", () => {
    const passages = parseGame("# Demo Game\n\nintro text\n\n## Setup\nlay out cards\n\n## Winning\nmost points");
    expect(passages.map((p) => p.section)).toEqual(["Overview", "Setup", "Winning"]);
    expect(passages.every((p) => p.game === "Demo Game")).toBe(true);
  });

  it("loads all four house games", () => {
    expect(new Set(corpus.map((p) => p.game)).size).toBe(4);
  });

  it("drops stopwords when tokenizing", () => {
    expect(tokenize("What does the Watchman do?")).toEqual(["watchman"]);
  });

  it("retrieves the Watchman passage for a Watchman question", () => {
    const top = retrieve(corpus, "What happens if the Watchman catches me?")[0];
    expect(top.game).toBe("Lantern Heist");
    expect(top.section).toBe("The Watchman");
  });

  it("returns nothing for an off-topic question and says so when formatted", () => {
    expect(retrieve(corpus, "zzz qqq")).toEqual([]);
    expect(formatPassages([])).toContain("no matching house rules");
  });
});
