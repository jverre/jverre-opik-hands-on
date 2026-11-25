import OpenAI from "openai";
import type { ChatCompletionMessageParam } from "openai/resources/chat/completions";
import { MODEL, SYSTEM_PROMPT } from "./hotel.js";
import { TOOL_DEFINITIONS, executeTool } from "./tools.js";

/** The slice of the OpenAI client the concierge needs (easy to stub in tests). */
export interface ChatClient {
  chat: { completions: { create: OpenAI["chat"]["completions"]["create"] } };
}

const MAX_TOOL_ROUNDS = 4;

/** One instance per guest conversation. Keeps the message history as memory. */
export class Concierge {
  readonly messages: ChatCompletionMessageParam[] = [{ role: "system", content: SYSTEM_PROMPT }];

  constructor(
    readonly conversationId: string,
    private readonly client: ChatClient,
  ) {}

  async answer(userMessage: string): Promise<string> {
    this.messages.push({ role: "user", content: userMessage });

    for (let round = 0; round < MAX_TOOL_ROUNDS; round++) {
      const response = await this.client.chat.completions.create({
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
          content: executeTool(call.function.name, call.function.arguments),
        });
      }
    }
    return "Sorry, I could not finish that request. Please call the front desk on extension 0.";
  }
}
