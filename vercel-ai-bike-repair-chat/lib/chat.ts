import { openai } from "@ai-sdk/openai";
import { convertToModelMessages, stepCountIs, streamText, type LanguageModel, type UIMessage } from "ai";
import { SYSTEM_PROMPT } from "./prompt";
import { runtimeContextFor, telemetrySettings } from "./telemetry";
import { tools } from "./tools";

export interface ChatRequest {
  id: string;
  messages: UIMessage[];
}

/** Parses and sanity-checks the JSON body that useChat (or the demo client) posts. */
export function parseChatRequest(body: unknown): ChatRequest {
  const { id, messages } = (body ?? {}) as Partial<ChatRequest>;
  if (typeof id !== "string" || !id) throw new Error("Missing chat id");
  if (!Array.isArray(messages) || messages.length === 0) throw new Error("Missing messages");
  return { id, messages };
}

/** One streamed assistant turn. The model is injectable so tests can pass a mock. */
export async function streamRepairReply(
  { id, messages }: ChatRequest,
  model: LanguageModel = openai("gpt-4o-mini"),
) {
  return streamText({
    model,
    system: SYSTEM_PROMPT,
    messages: await convertToModelMessages(messages),
    tools,
    stopWhen: stepCountIs(3), // allow tool call -> final answer without looping forever

    // The two settings below are the whole per-call Opik integration: the
    // telemetry settings emit AI SDK spans for the exporter registered in
    // instrumentation.node.ts, and runtimeContext carries the chat id that
    // becomes the Opik thread id, so each conversation is one thread.
    runtimeContext: runtimeContextFor(id),
    experimental_telemetry: telemetrySettings(),
  });
}
