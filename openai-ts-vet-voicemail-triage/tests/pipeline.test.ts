import { mkdtemp, readFile, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { describe, expect, it, vi } from "vitest";
import { createPipeline, type VoicemailClient } from "../src/pipeline.js";
import { VOICEMAILS } from "../src/voicemails.js";

// OPIK_TRACK_DISABLE=true is set in vitest.config.ts: track() still runs the function, it just
// sends nothing to Opik. These tests call the track()-wrapped pipeline to show it is unaffected.
function stubClient(urgency = "emergency") {
  const speech = vi.fn(async () => ({ arrayBuffer: async () => new TextEncoder().encode("fake-mp3").buffer as ArrayBuffer }));
  const transcribe = vi.fn(async () => "  Hi, this is Marisol Okafor.  ");
  const chat = vi.fn(async (_body: { messages: unknown[] }) => ({
    choices: [{ message: { content: JSON.stringify({ urgency, reason: "r", callback: { caller: "Marisol Okafor", phone: "555-0142", pet: "Biscuit", issue: "chocolate" } }) } }],
  }));
  const client = {
    audio: { speech: { create: speech }, transcriptions: { create: transcribe } },
    chat: { completions: { create: chat } },
  } as unknown as VoicemailClient;
  return { client, speech, transcribe, chat };
}

describe("voicemail pipeline (stubbed client, tracking disabled)", () => {
  it("synthesizes, transcribes and triages one voicemail", async () => {
    const dir = await mkdtemp(join(tmpdir(), "vm-"));
    const { client, speech, chat } = stubClient();
    const pipeline = createPipeline(client, dir);
    const vm = VOICEMAILS[0]!;

    const result = await pipeline.processVoicemail(vm);

    expect(speech).toHaveBeenCalledWith(expect.objectContaining({ voice: vm.voice, input: vm.script }));
    expect(await readFile(result.audioPath, "utf8")).toBe("fake-mp3");
    expect(result.transcript).toBe("Hi, this is Marisol Okafor.");
    expect(result.triage.urgency).toBe("emergency");
    // The transcript, not the original script, is what the model triages.
    expect(chat.mock.calls[0]![0].messages[1]).toEqual({ role: "user", content: "Hi, this is Marisol Okafor." });
  });

  it("reuses audio that already exists instead of calling TTS again", async () => {
    const dir = await mkdtemp(join(tmpdir(), "vm-"));
    const vm = VOICEMAILS[1]!;
    await writeFile(join(dir, `${vm.id}.mp3`), "cached");
    const { client, speech } = stubClient("urgent");
    await createPipeline(client, dir).processVoicemail(vm);
    expect(speech).not.toHaveBeenCalled();
  });
});
