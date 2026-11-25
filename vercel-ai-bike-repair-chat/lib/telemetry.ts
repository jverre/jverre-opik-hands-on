import { OpikExporter } from "opik-vercel";

export const PROJECT_NAME = "vercel-ai-bike-repair-chat";
export const TRACE_NAME = "workshop-chat-turn";

/** True when OPIK_TRACK_DISABLE=true. This is this app's own switch, not an SDK flag. */
export function trackingDisabled(env: Record<string, string | undefined> = process.env): boolean {
  return env.OPIK_TRACK_DISABLE === "true";
}

/**
 * Per-call telemetry settings for streamText. OpikExporter.getSettings turns
 * on span emission for this call and stores the trace name, which the exporter
 * uses as the Opik trace name (`workshop-chat-turn`).
 */
export function telemetrySettings(env: Record<string, string | undefined> = process.env) {
  return {
    ...OpikExporter.getSettings({ name: TRACE_NAME, isEnabled: !trackingDisabled(env) }),
    // Names the runtimeContext keys to copy onto the spans (threadId feeds Opik threads).
    includeRuntimeContext: { threadId: true, traceName: true },
  };
}

/** What streamText receives as runtimeContext; chat id becomes the Opik thread id. */
export function runtimeContextFor(chatId: string) {
  return { threadId: chatId, traceName: TRACE_NAME };
}

/**
 * Turns runtimeContext into the span attributes opik-vercel reads:
 * `ai.telemetry.metadata.threadId` groups traces into an Opik thread and
 * `ai.telemetry.metadata.traceName` names the trace.
 */
export function spanAttributes(runtimeContext?: Record<string, unknown>): Record<string, string> {
  const attributes: Record<string, string> = {};
  if (runtimeContext?.threadId != null) {
    attributes["ai.telemetry.metadata.threadId"] = String(runtimeContext.threadId);
  }
  if (runtimeContext?.traceName != null) {
    attributes["ai.telemetry.metadata.traceName"] = String(runtimeContext.traceName);
  }
  return attributes;
}
