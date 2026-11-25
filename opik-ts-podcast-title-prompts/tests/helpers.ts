import type { ChatClient } from "../src/copywriter.js";

/** A stand-in for the OpenAI client that records each request and returns a canned reply. */
export function stubClient(reply: string, calls: unknown[] = []): ChatClient {
  return {
    chat: {
      completions: {
        create: (async (params: unknown) => {
          calls.push(params);
          return { choices: [{ message: { content: reply } }] };
        }) as unknown as ChatClient["chat"]["completions"]["create"],
      },
    },
  };
}
