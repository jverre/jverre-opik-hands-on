# dspy-astronomy-fact-check

*A claim checker that teaches itself the house style: 0 of 8 suite items passing before compilation, 8 of 8 after.*

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![DSPy](https://img.shields.io/badge/DSPy-3.x-8B0000?style=flat)
![Opik SDK](https://img.shields.io/badge/Opik%20SDK-2.3-2f54eb?style=flat)

## The problem

The fact-check desk at the (fictional) Mirador Ridge Observatory wants every verdict in one rigid shape, so a script can read it:

```
REFUTED | cites: F08
NOT ENOUGH INFO | cites: none
```

Ask a language model to "check the claim against the fact sheet" and you get a correct but chatty paragraph ("The claim is false; the primary mirror is re-coated with aluminum...") that no script can parse. The shape exists only in the desk's habits. DSPy's answer is to stop hand-editing the prompt: you give an optimizer a few labeled examples and a metric, and it compiles demos into the prompt. The risk is that "the optimizer helped" is only a claim until you can see what changed. This example makes both halves visible in Opik.

## What you'll build

- A `dspy.ChainOfThought` program (`gpt-4o-mini`) that labels a claim `SUPPORTED`, `REFUTED` or `NOT ENOUGH INFO` against a ten-line offline fact sheet (`data/factsheet.txt`, ids F01 to F10).
- A strict metric (`verdict_metric`): exact format, right label, right fact id. It is plain Python, so compiling costs no judge tokens.
- `dspy.BootstrapFewShot`, which runs the program over eight labeled claims (`data/train.json`) and keeps up to five passing attempts as few-shot demos.
- An Opik test suite, `astronomy-claims`, with eight held-out claims (`data/test.json`). It runs once against the raw program and once against the compiled one.
- `OpikCallback` plus one `@opik.track` span, so every step is a trace.

## See it in Opik

Open the **`dspy-astronomy-fact-check`** project. It holds 22 traces from one run.

**Traces tab.** Sixteen are named `evaluation_task` (8 suite items times 2 programs). Open one: the tree is `check_claim` (general span) containing `ChainOfThought` and its `Predict` step, which wrap an `LM: openai - gpt-4o-mini` llm span with token counts and estimated cost; beside it are the judge spans (`llm_judge`, `metrics_calculation`). The other six traces are plain `ChainOfThought` traces: the teacher attempts BootstrapFewShot made during compilation, five of which passed the metric and became demos.

**The prompt is the evidence.** Compare the `LM:` span input of an uncompiled item with a compiled one. The raw prompt is about 2,000 characters: instructions, the fact sheet, the claim. The compiled prompts run to about 8,000, because five complete worked examples (claim, reasoning, `REFUTED | cites: F10`-style verdict) are now baked in. Nothing else changed, since the signature text is identical. Across all 22 LM spans, token usage and cost are filled in (about $0.008 in total).

**Experiments.** Two experiments on the `astronomy-claims` suite: `uncompiled` and `compiled`, 8 items each. In the run recorded here, `uncompiled` passes 0/8 and `compiled` passes 8/8. The uncompiled model was not wrong about the facts; it failed the two format assertions ("exactly `<LABEL> | cites: <FACT-ID>`", "nothing besides the label and tag") on every item and, with them, the label-and-citation assertion. Open the compare view to see the same eight rows flip together. Judge scoring can wobble, so a re-run may land an item lower.

## Run it yourself

1. Start a local Opik (`http://localhost:5173`, see the Opik self-hosting docs).
2. `cp .env.example .env` and set `OPENAI_API_KEY` (or keep keys in a parent folder's `.env`, which is picked up automatically).
3. `uv sync`
4. `uv run main.py` (about a minute; prints both pass rates and a link to the compare view).
5. Open the `dspy-astronomy-fact-check` project at `http://localhost:5173`.

Tests need no keys and no Opik: `env -u OPENAI_API_KEY OPIK_TRACK_DISABLE=true uv run pytest`.
For Opik Cloud, set `OPIK_API_KEY` and drop `OPIK_URL_OVERRIDE`.

## Poke around

- Set `max_bootstrapped_demos=1` in `factcheck.compile_program` and see which of the eight items fall back.
- Delete the NOT ENOUGH INFO rows from `data/train.json`. Watch what the compiled program says about "Who built Heliodor?".
- Add a fact F11 to the sheet and a claim that contradicts it to the test set. Does the compiled program cite the new id?
- Open a bootstrap-phase trace and compare the teacher's reasoning with what ends up as a demo.

## Gotchas we hit

**Correct answers fail with `0% passed (0/1)` on the item assertion.** The LLM judge sees only the claim and the answer, never the fact sheet. An assertion like "REFUTED because the staff has 23 astronomers" asks it to verify something it cannot see, so right answers fail. Keep per-item assertions checkable from the answer alone: `f"The answer's label is {label} and it cites {cites}"`.

**The compiled program answers `UNSUPPORTED` or `CANNOT BE DETERMINED` for unanswerable claims.** `BootstrapFewShot` stops once `max_bootstrapped_demos` attempts pass, taking the trainset in order. With four demos and a trainset whose NOT ENOUGH INFO rows came late, none made it in and the suite scored 6/8. Interleave the labels so each appears in the first few rows, as `data/train.json` now does.

**`WARNING dspy.utils.callback: Error when calling callback <OpikCallback ...>: assert None is not None` in tests.** With `OPIK_TRACK_DISABLE=true` there is no trace for the callback to attach to, so it warns on every call. Keep the callback out of offline tests: stub the program and call the `@opik.track`-decorated task directly (`tests/test_factcheck.py`).

## How it's put together

- `factcheck.py`: signature, program, verdict parser, metric, data loaders, `BootstrapFewShot` compile step, `OpikCallback` wiring, and the traced `check_claim` task.
- `main.py`: builds the suite, runs it on both programs with `opik.run_tests`, flushes, prints the comparison.
- `data/factsheet.txt`: the ten-fact observatory sheet. `data/train.json`: eight labeled claims for compiling. `data/test.json`: eight held-out claims for the suite.
- `tests/test_factcheck.py`: parser, metric, data consistency and an offline call of the traced task.

---

*built with Opik · inspired by Opik's examples and documentation*
