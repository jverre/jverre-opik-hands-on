import { Opik, getGlobalClient, getTrackContext, setGlobalClient, track } from "opik";
import { trackOpenAI } from "opik-openai";
import { writeEpisodeCopy, type ChatClient, type EpisodeCopy } from "./copywriter.js";
import type { Episode } from "./episodes.js";
import { loadNearestEnv } from "./env.js";
import type { PromptLoader } from "./library.js";
import { MODEL } from "./prompts.js";

export const PROJECT_NAME = "opik-ts-podcast-title-prompts";

let configured = false;

/**
 * One shared Opik client, installed as the SDK's global client. It reads
 * OPIK_URL_OVERRIDE / OPIK_WORKSPACE (and OPIK_API_KEY for Opik Cloud) from the
 * environment, so .env must load first. projectName decides which project every
 * trace lands in; making it the global client means track(), the integration
 * wrapper and test-suite runs all write through the same queue and project.
 */
export function getOpik(): Opik {
  if (!configured) {
    loadNearestEnv();
    setGlobalClient(new Opik({ projectName: PROJECT_NAME }));
    configured = true;
  }
  return getGlobalClient();
}

/** Flush buffered traces. Without this a short script can exit before anything is sent. */
export async function flushTraces(): Promise<void> {
  if (configured) await getGlobalClient().flush();
}

/**
 * Returns a copywriter that records every call as one trace named
 * "write-episode-copy". The prompt is loaded inside the traced function, and
 * the version and commit that actually ran are stamped on the trace metadata,
 * so any reply can be traced back to the wording that produced it.
 */
export function tracedCopywriter(
  rawClient: ChatClient,
  loadPrompt: PromptLoader,
): (episode: Episode) => Promise<EpisodeCopy> {
  const opik = getOpik();
  // track() opens a trace (root span) around the function: input is the episode,
  // output is the parsed copy, and anything traced inside becomes a child span.
  // type is set explicitly: without it the TS SDK files the root as an "llm" span
  // with no model or tokens, which muddies the Models and cost columns.
  // Inside a test-suite run it becomes a span under that run's evaluation_task trace.
  return track({ name: "write-episode-copy", projectName: PROJECT_NAME, type: "general" }, async (episode: Episode) => {
    const prompt = await loadPrompt();
    const context = getTrackContext();
    // Metadata on the trace is what you filter by in the traces table to compare versions.
    context?.trace.update({
      metadata: { prompt_name: prompt.name, prompt_version: prompt.version, prompt_commit: prompt.commit, model: MODEL },
    });
    // trackOpenAI wraps the client: each completion becomes a child span with the
    // model, token usage and (for known models) cost. Unlike track(), it does not
    // look up the active context, so parent is what nests it under this trace
    // instead of creating a second, separate trace per call.
    const client = trackOpenAI(rawClient, { client: opik, parent: context?.span, generationName: "episode-copy" });
    return writeEpisodeCopy(client, prompt.prompt, episode);
  }) as (episode: Episode) => Promise<EpisodeCopy>;
}
