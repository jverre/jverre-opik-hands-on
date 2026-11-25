import { describe, expect, it } from "vitest";
import { Concierge, type ChatClient } from "../src/concierge.js";

// Stub model: first asks for the spa tool, then answers using its result.
function stubClient(): ChatClient {
  let calls = 0;
  const create = async () => {
    calls += 1;
    const message =
      calls === 1
        ? {
            role: "assistant",
            content: null,
            refusal: null,
            tool_calls: [
              { id: "call_1", type: "function", function: { name: "check_spa_slots", arguments: '{"day":"today"}' } },
            ],
          }
        : { role: "assistant", content: "Two slots are open today.", refusal: null };
    return { choices: [{ index: 0, finish_reason: "stop", message }] };
  };
  return { chat: { completions: { create } } } as unknown as ChatClient;
}

describe("Concierge (tracking disabled, stub model)", () => {
  // OPIK_TRACK_DISABLE=true is set by vitest.config.ts, so the real tracing
  // wrapper runs here without sending anything.
  it("runs the tool loop and keeps history", async () => {
    const concierge = new Concierge("t-1", stubClient());
    const reply = await concierge.answer("Any spa slots today?");
    expect(reply).toBe("Two slots are open today.");
    expect(concierge.messages.map((m) => m.role)).toEqual(["system", "user", "assistant", "tool", "assistant"]);
    expect(concierge.messages[3]).toMatchObject({ role: "tool", tool_call_id: "call_1" });
  });
});
