import { Opik, getGlobalClient, getTrackContext, setGlobalClient, track } from "opik";
import { trackOpenAI } from "opik-openai";
import { writeEpisodeCopy, type ChatClient, type EpisodeCopy } from "./copywriter.js";
import type { Episode } from "./episodes.js";
import { loadNearestEnv } from "./env.js";

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
 * "write-episode-copy". `metadata` is stamped on the trace so you can filter
 * the traces table by which prompt produced them.
 */
export function tracedCopywriter(
  rawClient: ChatClient,
  systemPrompt: string,
  metadata: Record<string, unknown>,
): (episode: Episode) => Promise<EpisodeCopy> {
  const opik = getOpik();
  // track() opens a trace (root span) around the function: input is the episode,
  // output is the parsed copy, and anything traced inside becomes a child span.
  return track({ name: "write-episode-copy", projectName: PROJECT_NAME }, async (episode: Episode) => {
    const context = getTrackContext();
    context?.trace.update({ metadata });
    // trackOpenAI wraps the client: each completion becomes a child span with the
    // model, token usage and (for known models) cost. Unlike track(), it does not
    // look up the active context, so parent is what nests it under this trace
    // instead of creating a second, separate trace per call.
    const client = trackOpenAI(rawClient, { client: opik, parent: context?.span, generationName: "episode-copy" });
    return writeEpisodeCopy(client, systemPrompt, episode);
  }) as (episode: Episode) => Promise<EpisodeCopy>;
}
