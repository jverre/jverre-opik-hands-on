import { Opik, PromptType } from "opik";
import {
  BRIEF_NAME,
  BRIEF_TEMPLATES,
  V2_CHANGE_DESCRIPTION,
} from "./briefs.js";

export interface BriefVersion {
  version: string;
  template: string;
  promptId?: string;
}

// The briefs live in the Opik prompt library, not only in code. The first run
// seeds v1 and v2; later runs read them back, so editing a brief in the Opik UI
// (saving a v3) changes what the CLI sends next time.
export async function loadBriefs(
  opik: Opik,
  projectName: string,
  wanted: string[],
): Promise<Record<string, BriefVersion>> {
  // createPrompt compares against the latest version, so re-running it would
  // not dedupe v1 after v2 exists. Seed only when the prompt is missing.
  const existing = await opik.getPrompt({ name: BRIEF_NAME });
  if (!existing) {
    // Each createPrompt with changed text is saved as a new immutable version:
    // v1 then v2, visible with a diff under Prompt library in Opik.
    await opik.createPrompt({
      name: BRIEF_NAME,
      prompt: BRIEF_TEMPLATES.v1,
      type: PromptType.MUSTACHE,
      changeDescription: "Initial brief: scene, hero, mood",
      tags: ["image-generation", "storybook"],
      projectName,
    });
    await opik.createPrompt({
      name: BRIEF_NAME,
      prompt: BRIEF_TEMPLATES.v2,
      type: PromptType.MUSTACHE,
      changeDescription: V2_CHANGE_DESCRIPTION,
      tags: ["image-generation", "storybook"],
      projectName,
    });
    console.log(`Registered "${BRIEF_NAME}" in the prompt library (v1 + v2).`);
  }

  // getPrompt with a version name returns that immutable version's text, so a
  // v3 saved in the Opik UI can be requested with --briefs v3.
  const out: Record<string, BriefVersion> = {};
  for (const version of wanted) {
    const prompt = await opik.getPrompt({ name: BRIEF_NAME, version });
    if (!prompt) throw new Error(`Prompt "${BRIEF_NAME}" has no version ${version} in the library`);
    out[version] = { version, template: prompt.prompt, promptId: prompt.id };
  }
  return out;
}
