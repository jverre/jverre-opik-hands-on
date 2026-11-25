import OpenAI from "openai";
import { writeEpisodeCopy } from "./copywriter.js";
import { EPISODES } from "./episodes.js";
import { loadNearestEnv } from "./env.js";
import { PROMPT_V1, PROMPT_V2 } from "./prompts.js";

loadNearestEnv();

async function main(): Promise<void> {
  const client = new OpenAI();
  for (const [label, prompt] of [["v1", PROMPT_V1], ["v2", PROMPT_V2]] as const) {
    console.log(`\n=== Prompt ${label} ===`);
    for (const episode of EPISODES) {
      const copy = await writeEpisodeCopy(client, prompt, episode);
      console.log(`\n${episode.show} with ${episode.guest}\n  Title: ${copy.title}\n  Blurb: ${copy.blurb}`);
    }
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
