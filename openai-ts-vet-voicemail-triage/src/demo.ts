import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import OpenAI from "openai";
import { loadNearestEnv } from "./env.js";
import { createPipeline, type VoicemailClient, type VoicemailResult } from "./pipeline.js";
import { PROJECT_NAME, attachFileToTrace, chatWithTracing, flushTraces } from "./tracing.js";
import { buildCallbackList, describeCallback } from "./triage.js";
import { VOICEMAILS } from "./voicemails.js";

loadNearestEnv();
// Always talk to the public OpenAI API, even if the shell points at a proxy.
delete process.env.OPENAI_BASE_URL;

const AUDIO_DIR = join(dirname(fileURLToPath(import.meta.url)), "..", "data", "audio");

async function main(): Promise<void> {
  // A plain client for audio (those steps are traced by track() spans); chat calls are wrapped
  // per call by chatWithTracing so they land as llm spans inside the triage span.
  const pipeline = createPipeline(new OpenAI() as unknown as VoicemailClient, AUDIO_DIR, chatWithTracing);

  const results: VoicemailResult[] = [];
  for (const voicemail of VOICEMAILS) {
    console.log(`\n=== ${voicemail.id} ===`);
    const result = await pipeline.processVoicemail(voicemail);
    results.push(result);
    console.log(`Heard:  ${result.transcript}`);
    const match = result.triage.urgency === voicemail.expectedUrgency ? "matches" : "DIFFERS from";
    console.log(`Triage: ${result.triage.urgency} (${match} the vet tech's call: ${voicemail.expectedUrgency}) - ${result.triage.reason}`);
  }

  console.log("\n=== Callback list (most urgent first) ===");
  for (const item of buildCallbackList(results)) console.log(describeCallback(item.triage));

  // Flush so the traces exist on the server, then attach each trace's MP3. In the trace view the
  // audio is playable, so a mis-triaged message can be settled by listening to what was said.
  await flushTraces();
  for (const result of results) {
    if (result.traceId) await attachFileToTrace(result.traceId, result.audioPath, "audio/mpeg");
  }
  console.log(`\nDone. Open the ${PROJECT_NAME} project in Opik.`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
