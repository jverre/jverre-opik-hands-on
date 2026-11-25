import OpenAI from "openai";
import type { ChatCompletionMessageParam } from "openai/resources/chat/completions";
import { MODEL, SYSTEM_PROMPT } from "./hotel.js";
import { TurnTrace } from "./tracing.js";
import { TOOL_DEFINITIONS, executeTool } from "./tools.js";

/** The slice of the OpenAI client the concierge needs (easy to stub in tests). */
export interface ChatClient {
  chat: { completions: { create: OpenAI["chat"]["completions"]["create"] } };
}

const MAX_TOOL_ROUNDS = 4;

/** One instance per guest conversation. Keeps the message history as memory. */
export class Concierge {
  readonly messages: ChatCompletionMessageParam[] = [{ role: "system", content: SYSTEM_PROMPT }];
  /** Opik id of the most recent turn's trace, so feedback can be attached to it later. */
  lastTraceId: string | undefined;

  constructor(
    readonly conversationId: string,
    private readonly client: ChatClient,
  ) {}

  async answer(userMessage: string): Promise<string> {
    this.messages.push({ role: "user", content: userMessage });
    const turn = new TurnTrace(this.conversationId, userMessage, this.client);
    this.lastTraceId = turn.traceId;
    try {
      const reply = await this.runTurn(turn);
      turn.finish(reply);
      return reply;
    } catch (err) {
      turn.finish(`error: ${err instanceof Error ? err.message : String(err)}`);
      throw err;
    }
  }

  private async runTurn(turn: TurnTrace): Promise<string> {
    const client = turn.client;
    for (let round = 0; round < MAX_TOOL_ROUNDS; round++) {
      const response = await client.chat.completions.create({
        model: MODEL,
        messages: this.messages,
        tools: TOOL_DEFINITIONS,
      });
      const message = response.choices[0]?.message;
      if (!message) throw new Error("model returned no choices");
      this.messages.push(message);

      if (!message.tool_calls?.length) return message.content ?? "";

      for (const call of message.tool_calls) {
        if (call.type !== "function") continue;
        this.messages.push({
          role: "tool",
          tool_call_id: call.id,
          content: turn.runTool(call.function.name, call.function.arguments, () =>
            executeTool(call.function.name, call.function.arguments),
          ),
        });
      }
    }
    return "Sorry, I could not finish that request. Please call the front desk on extension 0.";
  }
}
