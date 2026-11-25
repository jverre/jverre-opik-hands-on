import { describe, expect, it } from "vitest";
import { MockLanguageModelV4 } from "ai/test";
import { simulateReadableStream } from "ai";
import { parseChatRequest, streamRepairReply } from "../lib/chat";
import { readReply, textDeltaFromLine } from "../scripts/sse";

const userMessage = { id: "m1", role: "user" as const, parts: [{ type: "text" as const, text: "Why does my chain squeak?" }] };

function mockModel(reply: string) {
  return new MockLanguageModelV4({
    doStream: async () => ({
      stream: simulateReadableStream({
        chunks: [
          { type: "text-start", id: "t" },
          { type: "text-delta", id: "t", delta: reply },
          { type: "text-end", id: "t" },
          { type: "finish", finishReason: { unified: "stop", raw: "stop" }, usage: { inputTokens: { total: 5, noCache: 5 }, outputTokens: { total: 4, text: 4 } } },
        ],
      }),
    }),
  } as never);
}

describe("chat request parsing", () => {
  it("accepts a useChat body and rejects an empty one", () => {
    expect(parseChatRequest({ id: "c1", messages: [userMessage] }).id).toBe("c1");
    expect(() => parseChatRequest({ id: "c1", messages: [] })).toThrow("Missing messages");
    expect(() => parseChatRequest(null)).toThrow("Missing chat id");
  });
});

describe("streaming reply with tracking disabled", () => {
  it("streams the model's text through the traced call path", async () => {
    // OPIK_TRACK_DISABLE=true switches the telemetry spans off; the call must still work.
    process.env.OPIK_TRACK_DISABLE = "true";
    const model = mockModel("Likely a dry chain. Wipe it and re-lube.");
    const result = await streamRepairReply({ id: "c1", messages: [userMessage] }, model);
    expect(await result.text).toBe("Likely a dry chain. Wipe it and re-lube.");
    expect(JSON.stringify(model.doStreamCalls[0].prompt)).toContain("Cobblestone Cycle Co-op");
  });

  it("serves the reply as an SSE stream the demo client can read", async () => {
    process.env.OPIK_TRACK_DISABLE = "true";
    const result = await streamRepairReply({ id: "c2", messages: [userMessage] }, mockModel("Check chain wear."));
    const response = result.toUIMessageStreamResponse();
    const chunks: string[] = [];
    const text = await readReply(response.body!, (d) => chunks.push(d));
    expect(text).toBe("Check chain wear.");
    expect(chunks.length).toBeGreaterThan(0);
  });
});

describe("sse parsing", () => {
  it("ignores non-text events", () => {
    expect(textDeltaFromLine('data: {"type":"text-delta","id":"a","delta":"hi"}')).toBe("hi");
    expect(textDeltaFromLine('data: {"type":"start"}')).toBe("");
    expect(textDeltaFromLine("data: [DONE]")).toBe("");
    expect(textDeltaFromLine("garbage")).toBe("");
  });
});
