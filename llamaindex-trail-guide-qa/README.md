# llamaindex-trail-guide-qa

*Ask a stack of PDF trail guides a question, then see which section answered it, and test that section by section.*

![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![LlamaIndex](https://img.shields.io/badge/llama--index-0.14%2B-6a4c93?style=flat)
![Opik 2.3.2](https://img.shields.io/badge/opik-2.3.2-2f54eb?style=flat)

Trail guides are repetitive on purpose. Every trail has an Overview, Hazards, Permits and Water section, so
"how much water is there?" matches four near-identical paragraphs, one per trail. If the bot answers with the
wrong trail's water sources, that is a safety problem, and the final answer alone will not tell you whether
retrieval picked the wrong section or the model misread the right one.

## What you'll build

A small LlamaIndex app over four invented trails (Heron Ridge Loop, Kestrel Pass Traverse, Old Quarry Trail,
Marrow Falls Trail). `trails.py` writes one PDF per trail with reportlab; `main.py` reads them, cuts each into
one chunk per section (tagged with its trail and section), embeds the 16 chunks with OpenAI, and answers with
`gpt-4o-mini` using the top 3 chunks. Opik's LlamaIndex callback records every query. An Opik test suite of 8
questions then checks each answer against the one section that holds the fact, using plain-English assertions
that an LLM judge scores.

## See it in Opik

Open the project **`llamaindex-trail-guide-qa`**. After one run it holds 13 traces: one `index_construction`
(16 embeddings), four `query` traces from the demo questions, and eight `evaluation_task` traces from the suite.

Open a `query` trace. Its spans show retrieval and synthesis separately: `retrieve` (with an `embedding` span
below it) holds the chunks that were fetched, and `synthesize` holds `templating` and an `llm` span for
`gpt-4o-mini`, with the exact prompt, the answer, about 376 tokens and a cost of roughly $0.00008. That split
tells you which half to fix: a wrong chunk in `retrieve` is an index problem, a right chunk with a wrong answer
in `synthesize` is a prompt problem.

Then open the experiment link printed at the end of the run (Test suites, `trail-guide-sections`). The run I
verified passed 8 of 8 items. Each item has the section-specific assertion ("The answer states an overnight
permit costs $18 per party"), a retrieval assertion ("retrieved_sections includes 'Kestrel Pass Traverse /
Permits'"), and two suite-wide ones: no invented figures, and the answer is about the trail that was asked about.
Each `evaluation_task` trace shows the query tree plus the judge's own spans (`llm_judge`, a `completion` span
on a small judge model). The terminal also prints a plain-Python "Retrieval hit rate" (8/8), which checks the
same thing without a judge.

## Run it yourself

1. Install [uv](https://docs.astral.sh/uv/) and have Opik running locally (default UI `http://localhost:5173`,
   API `http://localhost:5173/api/`) or set `OPIK_URL_OVERRIDE` / `OPIK_WORKSPACE` for yours.
2. `cp .env.example .env` and fill in `OPENAI_API_KEY`. The app also reads a `.env` one folder up.
3. `uv sync`
4. `uv run main.py` (about a minute; a few cents of OpenAI usage)
5. Open the `llamaindex-trail-guide-qa` project in Opik, then the experiment link printed at the end.

The PDFs in `docs/` are committed; `uv run trails.py` regenerates them, and `main.py` does so if the folder is empty.

## Poke around

- Change `similarity_top_k` to 1 in `build_query_engine`. Questions are still answered from one chunk each, so
  watch which items change in the `retrieve` span.
- Edit the Marrow Falls "Permits" text in `trails.py` (make the pass $8), regenerate, and re-run: only the
  assertions that pin the old figure should fail.
- Add a question about a trail that does not exist and watch what `retrieve` returns and whether the answer
  admits the guides do not cover it.
- Drop the trail name from the text prefix in `split_sections` and see whether the Water questions still land on
  the right trail.

## Gotchas we hit

**Half the suite failed with "the answer invents figures... not present in retrieved_sections".** The judge only
sees what the task function returns. My first task output held the answer and the section labels
(`Heron Ridge Loop / Overview`), not the chunk text, so every figure looked invented. The first run passed 4 of 8
items for that reason alone, even though retrieval hit the right section 8 of 8 times. Fix: return the text too
(`"retrieved_excerpts": [n.node.text for n in response.source_nodes]`) and word the assertion against that field.
The re-run passed 8 of 8.

**The project shows 13 traces, not the 4 questions you asked.** `index_construction` is one trace, and
`run_tests` runs each of the 8 suite items through the query engine, each as an `evaluation_task` trace. Filter by
trace name to separate the demo traffic from the suite.

## How it's put together

- `main.py` - section-level index, Opik callback setup, the demo questions, and the suite run.
- `suite.py` - the 8 suite items, global assertions, and the plain-Python `section_hit` check.
- `trails.py` - the four fictional trails and the reportlab PDF generator.
- `docs/` - the generated PDFs (committed so a clean clone runs).
- `tests/test_trail_guides.py` - offline tests: section splitting, suite shape, retrieval check, a stubbed
  response, and `@opik.track` with tracking disabled.
- `pyproject.toml`, `.python-version`, `.env.example` - dependencies (Python 3.12+), the pinned interpreter, and
  the keys needed.

Run the tests with no keys and no Opik server:

```
env -u OPENAI_API_KEY OPIK_TRACK_DISABLE=true uv run pytest
```

---

*built with Opik · inspired by Opik's examples and documentation*
