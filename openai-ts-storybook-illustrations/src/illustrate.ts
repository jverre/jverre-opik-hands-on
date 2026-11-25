import fs from "node:fs";
import path from "node:path";
import OpenAI from "openai";
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
  page: StoryPage;
  version: string;
  template: string;
  outDir: string;
}): Promise<Illustration> {
  const { openai, page, version, template, outDir } = opts;
  const prompt = renderBrief(template, pageVars(page));

  const result = await openai.images.generate({
    model: IMAGE_MODEL,
    prompt,
    n: 1,
    size: IMAGE_SIZE,
    quality: IMAGE_QUALITY,
  });
  const b64 = result.data?.[0]?.b64_json;
  if (!b64) throw new Error(`${IMAGE_MODEL} returned no image for ${page.id}`);

  fs.mkdirSync(outDir, { recursive: true });
  const file = path.join(outDir, `${version}-${page.id}.png`);
  fs.writeFileSync(file, Buffer.from(b64, "base64"));
  return { page, version, file, prompt };
}
