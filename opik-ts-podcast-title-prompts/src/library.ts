import type { Prompt } from "opik";
import { PROMPT_NAME, PROMPT_V1, PROMPT_V2 } from "./prompts.js";
import { PROJECT_NAME, getOpik } from "./tracing.js";

/** What the copywriter needs from a library prompt (a plain shape, easy to stub in tests). */
export interface LoadedPrompt {
  name: string;
  prompt: string;
  version?: string;
  commit?: string;
}

export type PromptLoader = () => Promise<LoadedPrompt>;

const CHANGES: Record<string, string> = {
  v1: "Initial version: a friendly tone and no rules.",
  v2: "Add house rules: titles of at most 6 words and no punctuation, one-sentence blurb naming the guest, no clickbait words.",
};

/**
 * Make sure the prompt library holds v1 and v2 of "episode-title-blurb".
 * createPrompt compares against the latest version only, so calling it again
 * with v1's text after v2 exists would add a v3 that is a copy of v1. Checking
 * for the version first keeps re-runs from piling up duplicates.
 */
export async function registerPromptVersions(): Promise<void> {
  const opik = getOpik();
  for (const [version, text] of [["v1", PROMPT_V1], ["v2", PROMPT_V2]] as const) {
    const existing = await opik.getPrompt({ name: PROMPT_NAME, version, projectName: PROJECT_NAME });
    if (existing) continue;
    // createPrompt writes a new immutable version (v1, v2, ...) into the Prompt
    // library tab, with this change description shown in the version history.
    await opik.createPrompt({
      name: PROMPT_NAME,
      prompt: text,
      projectName: PROJECT_NAME,
      changeDescription: CHANGES[version],
    });
  }
}

/**
 * Fetch a version from the library at run time (latest when version is omitted),
 * so editing the prompt in the Opik UI changes the app without a deploy.
 */
export async function fetchPrompt(version?: string): Promise<Prompt> {
  const prompt = await getOpik().getPrompt({ name: PROMPT_NAME, version, projectName: PROJECT_NAME });
  if (!prompt) throw new Error(`Prompt "${PROMPT_NAME}"${version ? ` ${version}` : ""} is not in the library`);
  return prompt;
}

/** A loader pinned to one version, or to the latest when none is given. */
export function libraryLoader(version?: string): PromptLoader {
  return () => fetchPrompt(version);
}

/** Git-style diff between two versions, the same comparison the Prompt library tab shows. */
export async function diffVersions(fromVersion: string, toVersion: string): Promise<string> {
  const versions = await (await fetchPrompt()).getVersions();
  const from = versions.find((v) => v.version === fromVersion);
  const to = versions.find((v) => v.version === toVersion);
  if (!from || !to) throw new Error(`Could not find ${fromVersion} and ${toVersion} in the version history`);
  return to.compareTo(from);
}
