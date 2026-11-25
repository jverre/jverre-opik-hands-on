# openai-ts-vet-voicemail-triage

*A vet clinic's answering machine, triaged by a model, with the audio one click away from every verdict.*

![TypeScript](https://img.shields.io/badge/TypeScript-strict-3178C6?style=flat&logo=typescript&logoColor=white)
![OpenAI SDK](https://img.shields.io/badge/openai-6.x-412991?style=flat&logo=openai&logoColor=white)
![Opik](https://img.shields.io/badge/opik-2.3.2-2f54eb?style=flat)

Monday morning at Willowbrook Animal Clinic (fictional, like every name and number here): four voicemails are waiting, and whoever calls back first should be the owner whose dog just ate a box of chocolate, not the one rescheduling a vaccine. A model can sort that pile in seconds. The risk is the case where it sorts wrongly and nobody can tell why, because all that is left in the log is text that was already a guess at what somebody said.

This example keeps the evidence. It builds the voicemails itself, turns them into a transcript, triages them into an urgency level plus a callback list, and records every step in Opik with the MP3 attached to the trace, so "why was this marked routine?" is answered by pressing play.

## What you'll build

A small Node/TypeScript pipeline on the OpenAI SDK, one Opik trace per voicemail:

1. **Speak.** The cheapest OpenAI voice model (`tts-1`) reads four scripted messages from `src/voicemails.ts` into MP3 files under `data/audio/` (git-ignored, regenerated whenever missing).
2. **Listen.** `gpt-4o-mini-transcribe` turns each MP3 back into text.
3. **Triage.** `gpt-4o-mini` returns JSON: `emergency`, `urgent` or `routine`, a one-sentence reason, and a callback entry (caller, phone, pet, issue).
4. **Sort.** The demo prints one callback list, emergencies first.

A second script runs a small Opik **test suite** against the triage step: judge assertions per message, each message run three times, an item passing when two of three runs pass.

## See it in Opik

Open the `openai-ts-vet-voicemail-triage` project (local default: http://localhost:5173). After `npm run demo` the Traces tab holds four `triage-voicemail` traces, one per message. Open any of them:

- The root span `triage-voicemail` has three children in order, `text-to-speech`, `speech-to-text` and `triage`, and `triage` contains the `OpenAI.chat` span. The `OpenAI.chat` span is the model call, with `gpt-4o-mini-2024-07-18`, roughly 380-410 tokens, and a cost of about $0.00009.
- `speech-to-text` output is the transcript the model actually saw. Compare it with the script: in my run the transcriber wrote "Tomas" for Tomasz and "Whitcomb" for Whitcombe. That is the kind of drift you only notice with the audio at hand.
- The trace has an **Attachments** entry named like `vm-calm-rat-poison.mp3` (about 270 KB). Click it and it plays in the browser. That message is the interesting one: the caller sounds relaxed ("no rush"), yet mentions rat poison and pale gums, and the model correctly rates it `emergency`.

Then the suite. The Datasets area has `vet-voicemail-triage-suite` (type: evaluation suite, 4 items), and its experiment lists 12 `evaluation_task` traces: 4 messages x 3 runs each. In my run every item passed 3 of 3 runs, so 4/4 items passed. Each evaluation trace shows the `triage` span, the judge's `llm_judge` spans, and the judge model's `llm` span (about 800-860 tokens each). The three-runs policy is why one unlucky judge answer can no longer flip a verdict.

## Run it yourself

1. `cd openai-ts-vet-voicemail-triage && npm install`
2. `cp .env.example .env` and set `OPENAI_API_KEY`. (A `.env` in any parent folder works too. Defaults point at a local Opik: `OPIK_URL_OVERRIDE=http://localhost:5173/api/`, `OPIK_WORKSPACE=default`. For Opik Cloud, change both and add `OPIK_API_KEY`.)
3. `npm run demo` synthesizes the audio (first run only), transcribes, triages, prints the callback list, then uploads each MP3 to its trace. About 20 seconds with audio cached, about a minute when it has to synthesize.
4. `npm run suite` builds the test suite and runs it (about 30 seconds). It prints the pass count per item and an experiment link.
5. `npm test` runs the offline tests. They need no keys and no Opik: the vitest config sets `OPIK_TRACK_DISABLE=true`, the SDK's switch that makes `track()` run the function and send nothing. Set the same variable in your own shell to run the demo code without tracing.

A full run (demo plus suite) costs a couple of cents.

## Poke around

- Delete `data/audio/` and re-run the demo. The `text-to-speech` span reappears in each trace; with audio cached, those traces only have `speech-to-text` and `triage`.
- In `src/triage.ts`, delete the line "Judge by what happened, not by how calm the caller sounds", then run `npm run suite`. The relaxed rat-poison message is the one to watch.
- Set `runsPerItem: 1, passThreshold: 1` in `src/suite.ts`, re-run a few times, and compare how much the pass count moves against the 3/2 policy. Note that the suite reuses an existing suite by name, so rename `SUITE_NAME` to see a fresh policy.
- Add a fifth voicemail with two pets or no phone number. The parser should return `null`, and a judge assertion about invented details should keep passing.

## Gotchas we hit

**The traces table shows 16 traces instead of 4, including ones named `OpenAI.chat` and `OpenAI.audio`.**
`trackOpenAI` opens its own top-level trace for every call unless it is told its parent, and it also wraps the audio endpoints. The fix is to hand it the running span as `parent`, and to use a plain client for the audio calls (their steps are already `track()` spans):
```ts
trackOpenAI(client, { client: getOpik(), parent: getTrackContext()?.span })
```
See `chatWithTracing` in `src/tracing.ts`.

**The model call's span type is `general`, not `llm`.**
In `opik-openai` 2.3.2 the integration marks every span it creates as `general`. Model, token usage and cost are still filled in (the cost column shows about $0.00009), so filter on those instead of the type column.

**The suite fails 0/3 on three of four items even though the triage looks right.**
My first scripts spelled numbers out ("five five five, zero one four two"). The suite feeds the script to the model as its transcript, the model returns `5550142`, and the judge decided the digits did not match. Writing the numbers as digits (`555-0142`) fixed it and matches what the transcriber returns for real audio. Lesson: a judge fails on formatting differences you never meant to test.

**No attachment helper in the TypeScript SDK.**
There is no `Attachment` class like the Python one, and the generated `attachments.uploadAttachment` call sends JSON, which cannot carry audio. `attachFileToTrace` in `src/tracing.ts` PUTs the raw bytes to `/v1/private/attachment/upload` instead. The trace must already exist on the server, so flush first.

## How it's put together

- `src/voicemails.ts`: the four fictional messages, each with a voice, the vet tech's expected urgency, and a per-message judge assertion.
- `src/triage.ts`: the prompt, the strict JSON parser (an unknown level throws instead of defaulting to routine), callback sorting and formatting.
- `src/pipeline.ts`: text-to-speech, speech-to-text and triage as `track()` spans under one `triage-voicemail` root.
- `src/tracing.ts`: the Opik client, flush, the chat wrapper and the attachment upload.
- `src/demo.ts`: runs all four voicemails, prints the callback list, uploads the MP3s.
- `src/suite.ts`: the test suite with the three-runs execution policy.
- `src/env.ts`: loads the nearest `.env`.
- `tests/triage.test.ts`: parser, sorting and phone formatting.
- `tests/pipeline.test.ts`: the pipeline with a stubbed client and tracking disabled.

---

*built with Opik · inspired by Opik's examples and documentation*
