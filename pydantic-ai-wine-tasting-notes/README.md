# pydantic-ai-wine-tasting-notes

**Sommelier scribbles in, typed records out, and a test suite that catches the values the model made up.**

![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![Pydantic AI](https://img.shields.io/badge/Pydantic%20AI-OpenTelemetry-E92063?style=flat)
![Opik](https://img.shields.io/badge/Opik-test%20suite-2f54eb?style=flat)

A tasting note is written for the person holding the glass: "92-93 maybe", "7/10 would
drink again", "2010... or 2011? label smudged". Ask a model for a typed record and it
returns something tidy every time, with a vintage, a score and a price in all the right
slots. Tidy is not the same as true. This project extracts a `TastingNote` from six
fictional notes with a Pydantic AI agent, sends every run to Opik as a trace, and then
runs a test suite whose assertions are all about one question: did the model write down
something the note never said?

## What you'll build

- A `tasting` package split into small modules: the `TastingNote` schema, the agent, a
  corpus loader, telemetry setup, the suite, and a CLI.
- A Pydantic AI agent on `gpt-4o-mini` whose `output_type` is `TastingNote`: wine, producer,
  vintage, region, grape, `score_100`, price, currency and a list of descriptors. Almost
  everything is optional, because real notes leave things out.
- Tracing through OpenTelemetry. Pydantic AI has no Opik callback, so logfire emits its
  spans, an OTLP exporter ships them to Opik, and `OpikSpanProcessor` nests them under the
  `@opik.track` function that wraps each extraction.
- An Opik test suite with four global rules and two or three plain-language assertions per
  note (for example "score_100 is null: 7/10 must not be converted to 70"), judged by
  `gpt-4o-mini` three times per item.

Three commands: `uv run tasting extract`, `uv run tasting batch`, `uv run tasting suite`.

## See it in Opik

Open the **pydantic-ai-wine-tasting-notes** project. After one `batch` plus one `suite` run
it holds 24 traces: 6 named `extract_note` (the batch) and 18 named `evaluation_task` (the
suite, six notes times three runs). Every trace has the same spine: an `extract_note` span
with the raw note as input and the record as output, an `invoke_agent agent` span below it,
and a `chat gpt-4o-mini` span of type `llm` that carries token counts and an estimated cost
(about $0.0001 for one extraction). The suite traces add the judge's spans beside it.

Open the Pauillac trace and you see a clean extraction: vintage 2016, `score_100` 94, price
142.0 in USD, grape "Cab Sauv". Now open the house-red trace. The note says "7/10 would
drink again" and the output says `score_100: 70`. The model quietly converted a
ten-point score to a hundred-point one. The Rioja trace is the second case: the note is
unsure between 2010 and 2011 and gives "92-93 maybe", and the record says `vintage: 2010`
and `score_100: 92`, no hesitation in sight.

Those are exactly the failures the suite reports. Under **Test suites**, open the
suite, then the **tasting-notes-gpt-4o-mini** experiment. In the run we checked, 4 of 6 items
passed (66.7%). House red and Rioja failed. The assertion "score_100 is null: 7/10 must not
be converted to 70" held in only 1 of 3 runs, and the Rioja assertion about an undecidable
vintage held in 2 of 3. The Barolo (forgotten score kept as null), the Sussex sparkling
(torn price tag kept as null) and the Chablis notes passed on all three runs. An honest
pass rate is the point: it is a number you can move by editing the prompt.

## Run it yourself

1. Install [uv](https://docs.astral.sh/uv/) and start Opik locally, or use Opik Cloud.
2. `cp .env.example .env` and fill in `OPENAI_API_KEY`. The Opik defaults target a local
   Opik at `http://localhost:5173/api/` (UI at `http://localhost:5173`). For cloud, set
   `OPIK_URL_OVERRIDE`, `OPIK_WORKSPACE` and `OPIK_API_KEY`.
3. `uv sync`
4. `uv run tasting extract --id house-red` for one note, or paste your own:
   `uv run tasting extract "Pommard 2017, 91 pts, EUR 55, cherry and clove"`
5. `uv run tasting batch` extracts all six notes (about two minutes on a busy server).
6. `uv run tasting suite` runs the test suite: 18 extractions plus an agentic judge, a few
   minutes and roughly six cents in total. It prints the pass rate, one line per item and
   the experiment link.
7. Offline tests: `OPIK_TRACK_DISABLE=true uv run pytest`. They need no keys and no Opik.

## Poke around

- Add "if a score is on a 10-point scale, multiply by ten" to `SYSTEM_PROMPT` in
  `tasting/agent.py`, re-run `suite`, and check whether the house-red assertion now fails on all three runs.
- Tighten the prompt the other way: tell the agent to return null whenever the note says
  "maybe", "or" or "?". Compare the two experiments side by side and see whether Rioja
  starts passing.
- Add a seventh note to `data/notes.json` and its assertions to `ASSERTIONS` in
  `tasting/suite.py`. The test `test_every_note_has_assertions` fails until you do.
- Change `runs_per_item` to 1 in `run_suite` and run twice. Compare the two pass rates: any
  difference is run-to-run noise, which is why the default is three runs and a threshold of two.

## Gotchas we hit

**`UserError: Set the OPENAI_API_KEY environment variable ... to use the OpenAI provider`
when importing the package.** Cause: `Agent("openai:gpt-4o-mini", ...)` resolves the
provider as soon as it is constructed, so a module-level agent needs a key just to import,
which breaks offline tests. Fix: build it lazily.

```python
@cache
def get_agent() -> Agent[None, TastingNote]:
    return Agent(MODEL, output_type=TastingNote, system_prompt=SYSTEM_PROMPT)
```

**The project holds 24 traces after running only six notes.** Cause: `opik.run_tests`
calls your task once per item per run, and because `extract_note` is traced, each call
becomes its own `evaluation_task` trace with the judge's spans in it. Fix: filter the trace
list by name (`extract_note` for the batch) or keep experiments in a separate project.

**The pass rate moves between runs.** Cause: both the extraction and the judge are
non-deterministic, and several assertions held in only 2 of 3 or 1 of 3 runs. Fix: give the
suite an execution policy instead of trusting one sample:
`global_execution_policy={"runs_per_item": 3, "pass_threshold": 2}`.

## How it's put together

- `tasting/schema.py`: the `TastingNote` Pydantic model.
- `tasting/agent.py`: the lazy Pydantic AI agent, the system prompt and the traced `extract_note`.
- `tasting/telemetry.py`: points logfire's OTLP export at Opik and adds `OpikSpanProcessor`.
- `tasting/corpus.py`: loads `data/notes.json`.
- `tasting/suite.py`: global and per-note assertions, suite creation and `run_tests`.
- `tasting/cli.py`: the `extract`, `batch` and `suite` commands, with a flush on exit.
- `tasting/config.py`: project name, model and `.env` loading.
- `data/notes.json`: six fictional sommelier notes.
- `tests/test_tasting.py`: offline tests with a stubbed model, including a traced call with tracking disabled.

*built with Opik · inspired by Opik's examples and documentation*
