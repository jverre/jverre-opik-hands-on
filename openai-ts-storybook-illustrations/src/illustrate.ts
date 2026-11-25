import fs from "node:fs";
import path from "node:path";
import OpenAI from "openai";
import type { Opik } from "opik";
import { trackOpenAI } from "opik-openai";
import { renderBrief } from "./briefs.js";
import { HERO, type StoryPage } from "./story.js";

// Cheapest gpt-image-1-mini setting: one 1024x1024 image at low quality.
export const IMAGE_MODEL = "gpt-image-1-mini";
export const IMAGE_SIZE = "1024x1024";
export const IMAGE_QUALITY = "low";

export interface Illustration {
  page: StoryPage;
  version: string;
  file: string;
  prompt: string;
}

export function pageVars(page: StoryPage): Record<string, string> {
  return { hero: HERO, scene: page.scene, mood: page.mood };
}

export async function illustratePage(opts: {
  openai: OpenAI;
  opik: Opik;
  page: StoryPage;
  version: string;
  template: string;
  outDir: string;
}): Promise<Illustration> {
  const { openai, opik, page, version, template, outDir } = opts;
  const prompt = renderBrief(template, pageVars(page));

  // One trace per page illustration; the brief version is a tag and metadata
  // so every picture in Opik says which brief produced it.
  const trace = opik.trace({
    name: "illustrate-page",
    input: { page: page.id, title: page.title, brief_version: version, prompt },
    tags: [version, page.id],
    metadata: { brief_version: version, model: IMAGE_MODEL, size: IMAGE_SIZE },
  });

  // trackOpenAI wraps the client: images.generate becomes an llm child span of
  // the trace above, holding the exact prompt sent to OpenAI.
  const tracked = trackOpenAI(openai, {
    client: opik,
    parent: trace,
    generationName: "images.generate",
  });

  let result;
  try {
    result = await tracked.images.generate({
      model: IMAGE_MODEL,
      prompt,
      n: 1,
      size: IMAGE_SIZE,
      quality: IMAGE_QUALITY,
    });
  } catch (error) {
    // Close the trace so a failed call still shows up (without an image).
    trace.update({ output: { error: String(error) } });
    trace.end();
    throw error;
  }
  const b64 = result.data?.[0]?.b64_json;
  if (!b64) {
    trace.end();
    throw new Error(`${IMAGE_MODEL} returned no image for ${page.id}`);
  }

  fs.mkdirSync(outDir, { recursive: true });
  const file = path.join(outDir, `${version}-${page.id}.png`);
  fs.writeFileSync(file, Buffer.from(b64, "base64"));

  // A large base64 data URI in the trace output is extracted by the Opik SDK
  // and uploaded as a real attachment: the trace shows the PNG, not base64 text.
  trace.update({
    output: { image: `data:image/png;base64,${b64}`, file },
  });
  trace.end();
  return { page, version, file, prompt };
}
