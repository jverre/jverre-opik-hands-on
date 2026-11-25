# opik-ts-podcast-title-prompts

**A title-and-blurb prompt for a podcast network, versioned in Opik and graded per version: v1 passes 0% of the suite, v2 passes 100%.**

![TypeScript](https://img.shields.io/badge/TypeScript-strict-3178C6?style=flat&logo=typescript&logoColor=white)
![Node](https://img.shields.io/badge/node-20%2B-339933?style=flat&logo=nodedotjs&logoColor=white)
![Opik SDK](https://img.shields.io/badge/opik-2.3.2-2f54eb?style=flat)
![OpenAI SDK](https://img.shields.io/badge/openai-6.49.0-412991?style=flat&logo=openai&logoColor=white)

Nobody writes a prompt once. Somebody tightens it, somebody else "just tries a tweak", and three weeks later the episode titles look different and no one can say which wording was live when. This example gives that problem a small, concrete home: the copy desk of a made-up indie network, **Marrow & Moss Audio**, which needs a title and a one-line blurb for every episode. The prompt lives in Opik's prompt library, each edit is a new immutable version, and a test suite grades every version against the network's house style, so "is v2 better?" has a number attached.

## What you'll build

A TypeScript app that takes an episode (show, guest, a few lines of notes) and asks `gpt-4o-mini` for `Title:` and `Blurb:` lines. Around it:

- **Two prompt versions** in the Opik prompt library under `episode-title-blurb`. v1 is a friendly "make people want to press play". v2 adds house rules: titles of at most 6 words with no punctuation, a one-sentence blurb that names the guest, and a ban on clickbait words (journey, unlock, dive, secrets...).
- **Run-time lookup.** The app fetches the prompt from the library on every call, and stamps the version and commit it used on the trace.
- **A test suite** of five episodes with four plain-language assertions, graded by an LLM judge (`gpt-4.1-mini`). Each episode is run three times and must pass at least two of them, because judges are noisy.
- **One experiment per version**, linked to the exact prompt version it tested, so the two runs can be put side by side.

The network's limit for titles is 8 words and the prompt asks for 6 on purpose: a model that aims at the limit lands on both sides of it.

## See it in Opik

Open the project **`opik-ts-podcast-title-prompts`**.

**Prompt library.** The prompt `episode-title-blurb` has two versions, v2 on top. Each carries its change description ("Initial version: a friendly tone and no rules." and "Add house rules: titles of at most 6 words and no punctuation, ..."). Compare v2 with v1 and the diff shows one line removed and seven added: the whole rule block. Nothing was edited in place; v1 is still there, byte for byte.

**Test suite and experiments.** The suite `episode-house-style` holds five items and four assertions. Its two experiments, `episode-title-blurb-v1` and `episode-title-blurb-v2`, each cover 15 runs (5 episodes x 3). In the run that produced this README:

| | v1 | v2 |
|---|---|---|
| Episodes passed | 0 of 5 | 5 of 5 |
| Title is 8 words or fewer | 0/15 runs | 15/15 |
| No colon, `?` or `!` in the title | 0/15 | 15/15 |
| Blurb is exactly one sentence | 0/15 | 15/15 |
| No clickbait words | 4/15 | 15/15 |

v1 fails because "engaging" reads as permission: titles like "Mapping Community: Dr. Priya Venkataraman's Transformative Journey in Cartography" with a four-sentence blurb. Judge verdicts vary from run to run, so a re-run can move a number or two (earlier runs of this same code gave v2 as 14/15 on the word limit); the gap between the versions does not.

**Traces.** Every experiment run is a trace named `evaluation_task` carrying `prompt_version` and `prompt_commit` in its metadata, so you can filter the traces table by `metadata.prompt_version`. Open one: the tree is `llm_task` > `write-episode-copy` > `episode-copy`. The last span holds the model (`gpt-4o-mini-2024-07-18`), token usage and an estimated cost. A separate `llm_judge` span holds the judge's call. The run also makes one stand-alone `write-episode-copy` trace from the live call that uses the latest prompt version.

## Run it yourself

1. Install Node 20 or newer, then in this folder: `npm install`.
2. `cp .env.example .env` and set `OPENAI_API_KEY` (a `.env` in any parent folder works too).
3. Point the SDK at your Opik. The `.env.example` default is a local install, `http://localhost:5173/api/` with workspace `default`. For Opik Cloud, change the URL and add `OPIK_API_KEY`.
4. `npm run demo`. It takes about 30 seconds and costs a few cents.
5. Open the `opik-ts-podcast-title-prompts` project in Opik (`http://localhost:5173` for a local install) and follow the tour above.

Run it again and nothing piles up: the prompt versions and suite items are only created when missing.

Offline tests (no keys, no Opik): `npm test`. `vitest.config.ts` sets `OPIK_TRACK_DISABLE=true`, the SDK's switch that turns tracing into a no-op.

## Poke around

- Weaken the rules in `PROMPT_V2` (say, drop the clickbait ban) and save the result as a new version `v3` in the Opik UI, then add it to the `for` loop in `src/demo.ts`: the last assertion should slide back toward v1's number.
- Add a third version that asks for a question-style title. The suite's second assertion should fail on it; check which assertion carries the verdict.
- Raise `runsPerItem` in `src/suite.ts` to 5 (and `passThreshold` to 3). How much does the pass rate wobble between runs?
- Add a sixth episode to `src/episodes.ts` with a guest whose name is long. Does the 8-word limit still hold?

## How it's put together

- `src/episodes.ts` - the five fictional episodes.
- `src/prompts.ts` - prompt v1 and v2, the model name, and how an episode becomes a user message.
- `src/copywriter.ts` - calls the model and parses the `Title:` / `Blurb:` reply.
- `src/tracing.ts` - the shared Opik client, `track()` around each episode, `trackOpenAI` for the model call, flush.
- `src/library.ts` - registers v1 and v2 in the prompt library, fetches a version at run time, prints the diff.
- `src/suite.ts` - the test suite, its assertions and execution policy, and the per-version `runTests` call.
- `src/demo.ts` - the whole walkthrough: register, diff, one live call, run both versions, print the comparison.
- `src/env.ts` - loads the nearest `.env`.
- `tests/copywriter.test.ts` - reply parsing and message building with a stubbed client.
- `tests/suite.test.ts` - suite item handling.
- `tests/tracing.test.ts` - the traced copywriter works with tracking disabled.
- `tests/helpers.ts` - the stub OpenAI client.

*built with Opik · inspired by Opik's examples and documentation*
