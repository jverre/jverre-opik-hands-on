<div align="center">

# openai-ts-storybook-illustrations

*Four picture-book pages, two versions of the art brief, every PNG attached to its trace.*

![Node](https://img.shields.io/badge/node-20%2B-5FA04E?style=flat&logo=node.js&logoColor=white)
![OpenAI SDK](https://img.shields.io/badge/openai-6.49-412991?style=flat&logo=openai&logoColor=white)
![Opik TS SDK](https://img.shields.io/badge/Opik%20TS%20SDK-2.3.2-2f54eb?style=flat)

</div>

Picture books are made of repeated requests: same hero, new scene, page after page. When the art direction changes ("softer, warmer, leave room for the text"), the change lives in a prompt, and the evidence lives in a folder of PNGs with no record of which wording made which one. This example is a small command-line illustrator for a fictional story, *Pip and the Lantern Moss*, written in TypeScript on the OpenAI SDK. The art brief is stored in Opik's prompt library as two versions, each page illustration is one trace, and the generated PNG is attached to that trace, so the brief and the picture sit together.

## What you'll build

A CLI (`src/cli.ts`) split into small modules: the story (`story.ts`), the brief templates (`briefs.ts`), the prompt-library loader (`library.ts`), the image call (`illustrate.ts`) and a read-back check (`check.ts`).

- **v1** of the brief is the bare scene plus a short hero description.
- **v2** adds what an art director would ask for after seeing v1: soft watercolor, a fixed full description of Pip, a calm top third for the story text, and no lettering.

`npm run demo` seeds both versions in the library (first run only), reads them back, then paints both story pages with each version: four images from `gpt-image-1-mini` at 1024x1024, low quality.

## See it in Opik

Open the **`openai-ts-storybook-illustrations`** project. The **Traces** tab holds four `illustrate-page` traces, tagged with the brief version (`v1` or `v2`) and the page id (`page-1-dusk`, `page-2-leaf-bridge`). Open one: the input shows the page and the fully rendered prompt, the metadata carries `brief_version`, `prompt_name`, `prompt_id` and the model, and the output panel shows the generated picture as an attachment (a PNG named `output-attachment-...-sdk.png`) instead of a block of base64.

Expand the trace and you find one span, `images.generate`. It is typed `general` rather than `llm`, but it has token usage (about 350 tokens for v1 pages and 410 for v2, of which 272 are image tokens) and an estimated cost of roughly $0.00016 to $0.00028 per image, computed by Opik from those tokens.

Then open **Prompt library** and select `storybook-page-brief`: two versions, v1 and v2, and the diff view highlights the sentences v2 added. In our run v2 did what it asked for on layout and look: both pages came back as watercolor with an empty, calm upper area, where v1 gave a darker, more painterly night scene with detail all the way up. It did not deliver consistency: the "identical on every page" Pip still changed shape, and on page 1 the v2 scarf turned into a red blob. Images differ run to run, so yours will vary. That is the point of the attachments: you judge each brief by looking at its traces, not by memory.

## Run it yourself

1. Start a local Opik (default API `http://localhost:5173/api/`, UI `http://localhost:5173`).
2. `cp .env.example .env` and set `OPENAI_API_KEY` (or keep it in a `.env` one folder up, which is also read).
3. `npm install`
4. `npm run demo` (about 40 seconds; four low-quality images cost a few cents at most).
5. `npm run check` reads the project back over REST and prints the traces, span usage, attachments and prompt version count.

Other commands: `npx tsx src/cli.ts run --briefs v2 --pages 1` (one image), `npx tsx src/cli.ts show` (print rendered briefs, no API calls).

## Poke around

- In the Opik prompt library, edit `storybook-page-brief` and save a v3 (say, "paint Pip's scarf as a plain red band"), then run `npx tsx src/cli.ts run --briefs v2,v3`. The CLI reads whatever the library holds, so the new traces are tagged `v3`.
- Add a third page in `src/story.ts` (a firefly crowd, say) and compare how the hero drifts across pages in the attachments.
- Run `npm test`: the tests stub OpenAI, so you can see the traced `illustratePage` run with tracking turned off.
- Open the `images.generate` span and compare input tokens for v1 and v2: the longer brief costs 60 more prompt tokens, while the image output is the same 272.

## Gotchas we hit

- **`npm install` fails with `ERESOLVE ... peer opik@"^1.8.61" from opik-openai@2.3.2`.** `opik-openai` declares a stale peer range for `opik`. Add an override so it reuses your pinned version:
  ```json
  "overrides": { "opik-openai": { "opik": "$opik" } }
  ```
- **`400 The model 'gpt-image-1' does not exist.`** Not every API key can use every image model. List what yours can with `GET https://api.openai.com/v1/models` and change `IMAGE_MODEL` in `src/illustrate.ts`. Ours had `gpt-image-1-mini`, which is also the cheapest.
- **The image span says `general`, not `llm`.** `trackOpenAI` wraps `images.generate` as a `general` span. Token usage, model and estimated cost are still filled in, so filter on the span name `images.generate` instead of the type.

## How it's put together

- `src/cli.ts`: the `run`, `show` and `check` commands; creates the Opik client and flushes it.
- `src/story.ts`: the fictional story, its two pages and Pip's description.
- `src/briefs.ts`: the v1 and v2 templates and the `{{variable}}` renderer.
- `src/library.ts`: seeds the brief into the Opik prompt library and reads versions back.
- `src/illustrate.ts`: one page, one trace, one `images.generate` call, PNG on disk and on the trace.
- `src/check.ts`: REST read-back of traces, spans, attachments and the prompt.
- `src/env.ts`: loads `.env` files.
- `tests/briefs.test.ts`: rendering, v2 rules, missing variables.
- `tests/illustrate.test.ts`: stubbed OpenAI run with `OPIK_TRACK_DISABLE=true` (set in `vitest.config.ts`) and the no-image error path.

Tests: `npm test` runs offline, no keys needed.

---

*built with Opik · inspired by Opik's examples and documentation*
