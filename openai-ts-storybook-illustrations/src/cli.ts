// Storybook illustrator CLI.
//   npm run demo                      illustrate every page with briefs v1 and v2
//   tsx src/cli.ts run --briefs v2    only one brief version
//   tsx src/cli.ts run --pages 1      only the first N pages
//   tsx src/cli.ts show               print the rendered briefs, no API calls

import process from "node:process";
import { parseArgs } from "node:util";
import OpenAI from "openai";
import { BRIEF_TEMPLATES, renderBrief } from "./briefs.js";
import { loadEnv } from "./env.js";
import { illustratePage, pageVars } from "./illustrate.js";
import { PAGES, STORY_TITLE } from "./story.js";

const OUT_DIR = "output";

async function run(versions: string[], pageCount: number): Promise<void> {
  if (!process.env.OPENAI_API_KEY) {
    throw new Error("OPENAI_API_KEY is not set. Add it to .env and re-run.");
  }
  const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
  console.log(`Illustrating "${STORY_TITLE}"`);
  for (const version of versions) {
    for (const page of PAGES.slice(0, pageCount)) {
      const done = await illustratePage({
        openai,
        page,
        version,
        template: BRIEF_TEMPLATES[version],
        outDir: OUT_DIR,
      });
      console.log(`  ${version} ${page.id} -> ${done.file}`);
    }
  }
}

function show(versions: string[], pageCount: number): void {
  for (const version of versions) {
    for (const page of PAGES.slice(0, pageCount)) {
      console.log(`[${version}] ${page.id}\n${renderBrief(BRIEF_TEMPLATES[version], pageVars(page))}\n`);
    }
  }
}

async function main(): Promise<void> {
  loadEnv();
  const { positionals, values } = parseArgs({
    allowPositionals: true,
    options: {
      briefs: { type: "string", default: "v1,v2" },
      pages: { type: "string", default: String(PAGES.length) },
    },
  });
  const versions = values.briefs!.split(",").map((v) => v.trim());
  for (const v of versions) {
    if (!BRIEF_TEMPLATES[v]) throw new Error(`Unknown brief version "${v}"`);
  }
  const pageCount = Math.min(Number(values.pages), PAGES.length);
  const command = positionals[0] ?? "run";
  if (command === "run") await run(versions, pageCount);
  else if (command === "show") show(versions, pageCount);
  else throw new Error(`Unknown command "${command}" (use run or show)`);
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : error);
  process.exit(1);
});
