import { readFile } from "node:fs/promises";
import { Opik, type Span } from "opik";
import { trackOpenAI } from "opik-openai";
import type { VoicemailClient } from "./pipeline.js";

export const PROJECT_NAME = "openai-ts-vet-voicemail-triage";

// The SDK reads the project from this variable, for both the explicit client and track().
// Set it before the first client is created, otherwise traces land in "Default Project".
process.env.OPIK_PROJECT_NAME = PROJECT_NAME;

let client: Opik | undefined;

/** One shared Opik client: it batches traces in memory and sends them in the background. */
export function getOpik(): Opik {
  client ??= new Opik({ projectName: PROJECT_NAME });
  return client;
}

/** Without this, a short-lived script can exit before the batched traces are sent. */
export async function flushTraces(): Promise<void> {
  await getOpik().flush();
}

function apiBase(): string {
  return (process.env.OPIK_URL_OVERRIDE ?? "http://localhost:5173/api/").replace(/\/+$/, "");
}

/**
 * Attach a local file to a trace. The TypeScript SDK has no attachment helper yet, so this calls
 * the REST upload endpoint directly (raw bytes, PUT). In Opik the trace then shows the file in its
 * Attachments area, and audio plays in the browser. Call it after flushTraces(): the trace must
 * already exist on the server.
 */
export async function attachFileToTrace(traceId: string, filePath: string, mimeType: string): Promise<void> {
  const body = await readFile(filePath);
  const fileName = filePath.split("/").pop() ?? "attachment";
  const query = new URLSearchParams({
    file_name: fileName,
    project_name: PROJECT_NAME,
    mime_type: mimeType,
    entity_type: "trace",
    entity_id: traceId,
  });
  const headers: Record<string, string> = {
    "Content-Type": mimeType,
    "Comet-Workspace": process.env.OPIK_WORKSPACE ?? "default",
  };
  if (process.env.OPIK_API_KEY) headers.Authorization = process.env.OPIK_API_KEY;
  const response = await fetch(`${apiBase()}/v1/private/attachment/upload?${query}`, {
    method: "PUT",
    headers,
    body,
  });
  if (!response.ok) throw new Error(`attachment upload failed: ${response.status} ${await response.text()}`);
}

/**
 * trackOpenAI wraps the client: each chat completion becomes an llm span with model, token usage
 * and cost. Passing `parent` nests that span under the running track() span; without it the SDK
 * opens a separate top-level trace for every call (and one per audio call too).
 */
export function chatWithTracing(client: VoicemailClient, parent: Span | undefined): VoicemailClient {
  return trackOpenAI(client, { client: getOpik(), parent }) as VoicemailClient;
}
