import { Opik, type Trace } from "opik";
import { trackOpenAI } from "opik-openai";
import { loadNearestEnv } from "./env.js";
import type { ChatClient } from "./concierge.js";

export const PROJECT_NAME = "openai-ts-hotel-concierge";

let client: Opik | undefined;

/**
 * One shared Opik client. It reads OPIK_URL_OVERRIDE / OPIK_WORKSPACE (and
 * OPIK_API_KEY for Opik Cloud) from the environment, so .env must load first.
 * projectName decides where every trace lands in the Opik UI.
 */
export function getOpik(): Opik {
  if (!client) {
    loadNearestEnv();
    client = new Opik({ projectName: PROJECT_NAME });
  }
  return client;
}

/** Flush buffered traces. Without this a short script can exit before anything is sent. */
export async function flushTraces(): Promise<void> {
  await client?.flush();
}

/** Everything one guest message needs to appear in Opik as a single trace. */
export class TurnTrace {
  private readonly trace: Trace;

  constructor(
    conversationId: string,
    userMessage: string,
    private readonly rawClient: ChatClient,
  ) {
    // One trace per guest message. threadId groups the turns of a conversation
    // into one row in the Threads tab; input/output become the thread transcript.
    this.trace = getOpik().trace({
      name: "concierge-turn",
      threadId: conversationId,
      input: { message: userMessage },
    });
  }

  get traceId(): string {
    return this.trace.data.id;
  }

  /**
   * trackOpenAI wraps the client: each completion becomes an llm span under this
   * trace, with token usage and (for known models) estimated cost. parent is
   * what keeps the spans inside the turn instead of creating separate traces.
   */
  get client(): ChatClient {
    return trackOpenAI(this.rawClient, {
      client: getOpik(),
      parent: this.trace,
      generationName: "concierge-completion",
    });
  }

  /** Record a tool call as a "tool" span so you can see what the model asked for and got back. */
  runTool(name: string, rawArgs: string, execute: () => string): string {
    const span = this.trace.span({ name, type: "tool", input: { arguments: rawArgs } });
    const result = execute();
    span.update({ output: { result } });
    span.end();
    return result;
  }

  finish(reply: string): void {
    this.trace.update({ output: { reply } });
    this.trace.end();
  }
}
