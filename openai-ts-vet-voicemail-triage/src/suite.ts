import OpenAI from "openai";
import { runTests } from "opik";
import { loadNearestEnv } from "./env.js";
import { createPipeline, type VoicemailClient } from "./pipeline.js";
import { PROJECT_NAME, chatWithTracing, flushTraces, getOpik } from "./tracing.js";
import { VOICEMAILS } from "./voicemails.js";

loadNearestEnv();
delete process.env.OPENAI_BASE_URL;

export const SUITE_NAME = "vet-voicemail-triage-suite";
export const JUDGE_MODEL = "gpt-4o-mini";

// Assertions every item must satisfy; an LLM judge reads the task's input and output to decide.
export const GLOBAL_ASSERTIONS = [
  "The urgency level fits the clinical risk in the message: poisoning, pale gums, collapse or " +
    "trouble breathing are never 'routine', and a pure scheduling request is never 'emergency'.",
  "The callback entry names a caller and a phone number only if they appear in the transcript, " +
    "and the phone digits match what the caller said. Nothing is invented.",
];

async function main(): Promise<void> {
  const opik = getOpik();

  // A test suite is a dataset whose items carry judge assertions. The execution policy is the
  // flakiness fix: the summarizer and the judge are both small LLMs, so each item runs three
  // times and passes if at least two runs pass. It is stored on the suite, visible in Opik.
  const suite = await opik.getOrCreateTestSuite({
    name: SUITE_NAME,
    projectName: PROJECT_NAME,
    description: "Does triage rate poisonings as emergencies and keep the callback details faithful?",
    globalAssertions: GLOBAL_ASSERTIONS,
    globalExecutionPolicy: { runsPerItem: 3, passThreshold: 2 },
  });

  // Items hold the spoken script as the transcript, so the suite needs no audio or TTS calls.
  // Re-runs reuse items that are already in the suite.
  const existing = new Set((await suite.getItems()).map((item) => String(item.data.voicemail_id)));
  const fresh = VOICEMAILS.filter((vm) => !existing.has(vm.id)).map((vm) => ({
    data: { voicemail_id: vm.id, transcript: vm.script },
    assertions: [vm.assertion],
  }));
  if (fresh.length > 0) await suite.insert(fresh);

  const { triage } = createPipeline(new OpenAI() as unknown as VoicemailClient, "data/audio", chatWithTracing);

  // runTests runs the task 3x per item, has the judge score every assertion, and records one
  // experiment in Opik with a pass/fail verdict per item and per run.
  const result = await runTests({
    testSuite: suite,
    model: JUDGE_MODEL,
    task: async (item) => {
      const transcript = String(item.transcript);
      return { input: { transcript }, output: await triage(transcript) };
    },
  });

  await flushTraces();
  console.log(`\nItems passed: ${result.itemsPassed}/${result.itemsTotal} (pass rate ${result.passRate})`);
  for (const item of result.itemResults.values()) {
    console.log(`  ${item.datasetItemId}: ${item.runsPassed}/${item.runsTotal} runs passed (need ${item.passThreshold})`);
  }
  if (result.experimentUrl) console.log(`Experiment: ${result.experimentUrl}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
