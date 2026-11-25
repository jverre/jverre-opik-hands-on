/**
 * Offline rules corpus: one markdown file per house game in data/rules,
 * split into one passage per "## Section". Retrieval is plain keyword
 * overlap, so the example needs no embeddings and no vector store.
 */
import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";

export interface Passage {
  game: string;
  section: string;
  text: string;
}

const STOPWORDS = new Set(
  `a an and are as at be but by can do does for from how i if in is it its my of on or so
  that the their then there they this to up us we what when where which who will with you your
  get got have has had not no yes any may one more most per play player players turn`.split(/\s+/)
);

export function tokenize(text: string): string[] {
  return text
    .toLowerCase()
    .split(/[^a-z0-9]+/)
    .filter((t) => t.length > 1 && !STOPWORDS.has(t));
}

/** Split one game's markdown into passages: "# Game" then "## Section" blocks. */
export function parseGame(markdown: string): Passage[] {
  const lines = markdown.split("\n");
  const game = (lines.find((l) => l.startsWith("# ")) ?? "# Unknown").slice(2).trim();
  const passages: Passage[] = [];
  let section = "Overview";
  let buffer: string[] = [];
  const flush = () => {
    const text = buffer.join(" ").trim();
    if (text) passages.push({ game, section, text });
    buffer = [];
  };
  for (const line of lines) {
    if (line.startsWith("# ")) continue;
    if (line.startsWith("## ")) {
      flush();
      section = line.slice(3).trim();
    } else {
      buffer.push(line.trim());
    }
  }
  flush();
  return passages;
}

export function loadCorpus(dir: string): Passage[] {
  return readdirSync(dir)
    .filter((f) => f.endsWith(".md"))
    .sort()
    .flatMap((f) => parseGame(readFileSync(path.join(dir, f), "utf8")));
}

/**
 * Score every passage by how many distinct query words it contains; words
 * that appear in the game's title or the section heading count double, so
 * "Lantern Heist" questions land in Lantern Heist even with vague wording.
 */
export function retrieve(corpus: Passage[], query: string, k = 3): Passage[] {
  const words = new Set(tokenize(query));
  const scored = corpus.map((p) => {
    const body = new Set(tokenize(p.text));
    const label = new Set(tokenize(`${p.game} ${p.section}`));
    let score = 0;
    for (const w of words) {
      if (label.has(w)) score += 2;
      else if (body.has(w)) score += 1;
    }
    return { p, score };
  });
  return scored
    .filter((s) => s.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, k)
    .map((s) => s.p);
}

export function formatPassages(passages: Passage[]): string {
  if (passages.length === 0) return "(no matching house rules found)";
  return passages.map((p) => `[${p.game} / ${p.section}] ${p.text}`).join("\n\n");
}
