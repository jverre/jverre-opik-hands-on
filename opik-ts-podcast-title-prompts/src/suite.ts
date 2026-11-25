import { runTests, type Prompt, type TestSuite, type TestSuiteResult } from "opik";
import type { EpisodeCopy } from "./copywriter.js";
import { EPISODES, type Episode } from "./episodes.js";
import { MODEL, PROMPT_NAME } from "./prompts.js";
import { PROJECT_NAME, getOpik } from "./tracing.js";

export const SUITE_NAME = "episode-house-style";
export const JUDGE_MODEL = "gpt-4.1-mini";

/**
 * The house style, written as plain-language assertions. An LLM judge checks every
 * one against each generated title and blurb; an item passes only if all hold.
 */
export const ASSERTIONS = [
  "The title is 8 words or fewer",
  "The title contains no colon, question mark or exclamation mark",
  "The blurb is exactly one sentence",
  "Neither the title nor the blurb uses clickbait words such as journey, unlock, unveil, dive, secrets, ultimate or \"you won't believe\"",
];

/** Judges are noisy, so each episode is run 3 times and must pass at least 2 of them. */
export const EXECUTION_POLICY = { runsPerItem: 3, passThreshold: 2 };

/** Pull the episode back out of a suite item (the item also carries its id). */
export function episodeFromItem(item: Record<string, unknown>): Episode {
  const { show, guest, notes } = item;
  if (typeof show !== "string" || typeof guest !== "string" || typeof notes !== "string") {
    throw new Error(`Suite item is not an episode: ${JSON.stringify(item)}`);
  }
  return { show, guest, notes };
}

/** Create the suite once (global assertions + policy), keep its assertions current, and add the episodes if it is empty. */
export async function ensureSuite(): Promise<TestSuite> {
  // A test suite is a dataset whose items carry assertions: it shows up under the
  // project's Test suites tab and every run of it becomes an experiment.
  const suite = await getOpik().getOrCreateTestSuite({
    name: SUITE_NAME,
    projectName: PROJECT_NAME,
    globalAssertions: ASSERTIONS,
    globalExecutionPolicy: EXECUTION_POLICY,
  });
  // getOrCreate keeps whatever assertions the suite was first created with, so
  // push the ones in this file whenever they differ. The code stays the source of truth.
  const current = await suite.getGlobalAssertions();
  if (JSON.stringify(current) !== JSON.stringify(ASSERTIONS)) {
    await suite.updateTestSettings({ globalAssertions: ASSERTIONS, globalExecutionPolicy: EXECUTION_POLICY });
  }
  if (!(await suite.getItemsCount())) {
    await suite.insert(EPISODES.map((episode) => ({ data: { ...episode } })));
  }
  return suite;
}

/** Run the suite once against one prompt version; the run is an experiment linked to that version. */
export async function runSuiteForVersion(
  suite: TestSuite,
  prompt: Prompt,
  write: (episode: Episode) => Promise<EpisodeCopy>,
): Promise<TestSuiteResult> {
  // runTests runs the task on every item (3 runs each), has the judge model score
  // the assertions, and records an experiment named after the version. Passing
  // prompts links the experiment to that exact prompt version in the UI.
  return runTests({
    testSuite: suite,
    projectName: PROJECT_NAME,
    experimentName: `${PROMPT_NAME}-${prompt.version}`,
    experimentConfig: { prompt_version: prompt.version, prompt_commit: prompt.commit, model: MODEL },
    prompts: [prompt],
    model: JUDGE_MODEL,
    taskThreads: 5,
    task: async (item) => {
      const episode = episodeFromItem(item);
      // Structured output: with a plain "Title: ..." string the judge counted the
      // label's own colon against the "no colon" rule.
      return { input: episode, output: await write(episode) };
    },
  });
}

/** Per-assertion tally across every run of a suite result: how often each house rule held. */
export function assertionBreakdown(result: TestSuiteResult): { assertion: string; passed: number; total: number }[] {
  const tally = new Map<string, { passed: number; total: number }>();
  for (const item of result.itemResults.values()) {
    for (const run of item.testResults) {
      for (const score of run.scoreResults) {
        const entry = tally.get(score.name) ?? { passed: 0, total: 0 };
        entry.total += 1;
        if (score.value === 1) entry.passed += 1;
        tally.set(score.name, entry);
      }
    }
  }
  return ASSERTIONS.flatMap((assertion) => {
    const entry = tally.get(assertion);
    return entry ? [{ assertion, ...entry }] : [];
  });
}
