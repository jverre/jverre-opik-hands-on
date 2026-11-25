import OpenAI from "openai";
import { EPISODES } from "./episodes.js";
import { loadNearestEnv } from "./env.js";
import { diffVersions, fetchPrompt, libraryLoader, registerPromptVersions } from "./library.js";
import { PROMPT_NAME } from "./prompts.js";
import { assertionBreakdown, ensureSuite, runSuiteForVersion } from "./suite.js";
import { PROJECT_NAME, flushTraces, tracedCopywriter } from "./tracing.js";

loadNearestEnv();

async function main(): Promise<void> {
  const openai = new OpenAI();

  // 1. Prompt library: v1 and v2 of the prompt, then the diff between them.
  await registerPromptVersions();
  // compareTo prints the git-style diff itself (the same change the Prompt library tab highlights).
  console.log(`=== ${PROMPT_NAME}: v1 -> v2 ===`);
  await diffVersions("v1", "v2");

  // 2. One live call that uses whatever version is latest in the library.
  const episode = EPISODES[0]!;
  const latest = await fetchPrompt();
  const copy = await tracedCopywriter(openai, libraryLoader())(episode);
  console.log(`Latest prompt (${latest.version}) for ${episode.show}:\n  Title: ${copy.title}\n  Blurb: ${copy.blurb}\n`);

  // 3. The same suite, once per prompt version. Each run is an experiment in Opik.
  const suite = await ensureSuite();
  const results: Record<string, Awaited<ReturnType<typeof runSuiteForVersion>>> = {};
  for (const version of ["v1", "v2"]) {
    const prompt = await fetchPrompt(version);
    results[version] = await runSuiteForVersion(suite, prompt, tracedCopywriter(openai, libraryLoader(version)));
  }

  // 4. Compare the two versions.
  console.log("\n=== Prompt version comparison ===");
  for (const [version, result] of Object.entries(results)) {
    const rate = result.passRate === undefined ? "n/a" : `${Math.round(result.passRate * 100)}%`;
    console.log(`${PROMPT_NAME} ${version}: ${rate} pass rate (${result.itemsPassed}/${result.itemsTotal} episodes passed)`);
    for (const { assertion, passed, total } of assertionBreakdown(result)) {
      console.log(`    ${passed}/${total} runs  ${assertion}`);
    }
  }

  // Send everything still buffered before the process exits.
  await flushTraces();
  console.log(`\nProject "${PROJECT_NAME}" now holds the prompt, the suite and both runs.`);
  for (const result of Object.values(results)) if (result.experimentUrl) console.log(result.experimentUrl);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
