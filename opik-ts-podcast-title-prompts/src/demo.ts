import OpenAI from "openai";
import { EPISODES } from "./episodes.js";
import { loadNearestEnv } from "./env.js";
import { MODEL, PROMPT_NAME, PROMPT_V1, PROMPT_V2 } from "./prompts.js";
import { PROJECT_NAME, flushTraces, tracedCopywriter } from "./tracing.js";

loadNearestEnv();

async function main(): Promise<void> {
  const openai = new OpenAI();
  for (const [label, prompt] of [["v1", PROMPT_V1], ["v2", PROMPT_V2]] as const) {
    console.log(`\n=== Prompt ${label} ===`);
    const write = tracedCopywriter(openai, prompt, { prompt_name: PROMPT_NAME, prompt_version: label, model: MODEL });
    for (const episode of EPISODES) {
      const copy = await write(episode);
      console.log(`\n${episode.show} with ${episode.guest}\n  Title: ${copy.title}\n  Blurb: ${copy.blurb}`);
    }
  }
  // Send everything still buffered before the process exits.
  await flushTraces();
  console.log(`\nTraces are in the Opik project "${PROJECT_NAME}".`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
