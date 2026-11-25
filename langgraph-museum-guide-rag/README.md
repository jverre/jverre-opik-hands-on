<div align="center">

# Museum Guide RAG

**`langgraph-museum-guide-rag`**

*Ask a museum guide a two-part question, then see in Opik whether retrieval brought both halves of the answer.*

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![LangGraph](https://img.shields.io/badge/langgraph-1.2-1C3C3C?style=flat)
[![Opik](https://img.shields.io/badge/Opik-2.3-2f54eb?style=flat)](https://github.com/comet-ml/opik)
[![uv](https://img.shields.io/badge/setup-uv-DE5FE9?style=flat&logo=uv&logoColor=white)](https://docs.astral.sh/uv/)

**[What you'll build](#what-youll-build) · [See it in Opik](#see-it-in-opik) · [Run it yourself](#run-it-yourself) · [Poke around](#poke-around) · [Gotchas](#gotchas-we-hit)**

</div>

---

Visitors ask museums questions that span two pages of a guide: "When does the
Orrery Room close, *and* can I get there without stairs?" The closing time lives
in the opening-hours section, the lift lives in the accessibility section. A RAG
assistant that fetches only one of them will still answer politely and fluently,
and nothing in the reply tells you half the question was dropped. This example
is a small assistant for the Alderbank Museum of Tides and Timekeeping (a
fictional place) that makes that failure visible: every question is a trace in
Opik showing exactly which guide sections were retrieved, and two experiments
over the same nine questions, one retrieving four sections and one retrieving a
single section, put numbers on the difference.

## What you'll build

A two-node LangGraph graph, **retrieve** then **generate**, over a guide split
into twenty sections (`data/*.md`: galleries, visiting, accessibility, famous
pieces). `retrieve` embeds the question with `text-embedding-3-small` and takes
the top *k* sections from an in-memory vector store (k = 4 by default);
`generate` answers with `gpt-4o-mini` using only those sections. The code is
split into small modules (`guide/corpus.py`, `retrieval.py`, `graph.py`,
`evaluation.py`) and `main.py` wires them together: it asks four questions, then
creates an Opik dataset of nine questions and runs the experiment twice, as
`k4-baseline` and `k1-starved`, scoring each run with Opik's `Hallucination` and
`ContextPrecision` judges.

## See it in Opik

Open the **`langgraph-museum-guide-rag`** project (on a local install that is
`http://localhost:5173`). After one run, the **Traces** tab holds 22 traces:
four named `LangGraph` (the four demo questions) and eighteen named
`evaluation_task` (nine dataset questions times two experiments).

Click a `LangGraph` trace, for example the one for "Is there a planetarium show
at the museum?". The tree mirrors the graph: a `retrieve` span containing a
`vector_search` span (type **tool**, input is the question and `k=4`, output is
the four retrieved sections), then a `generate` span containing the `ChatOpenAI`
**llm** span with the full prompt, the answer ("I don't know."), 436 tokens and
an estimated cost of $0.0000672. Every one of the 58 llm spans in the project
carries a cost. An `evaluation_task` trace has the same graph nested under a
`task` span, next to a `metrics_calculation` span where each judge appears as its
own llm span with its reasoning.

Then open **Experiments**. You will see `k4-baseline` and `k1-starved` linked to
the `museum-guide-questions` dataset, with `k`, `model` and `judge` as config
columns. In the run that produced these numbers, `k4-baseline` averaged
`hallucination_metric` 0.01 and `context_precision_metric` 0.76, and
`k1-starved` averaged 0.00 and 0.67. Tick both and use **Compare** to see the
rows side by side; two of them tell the story:

- *"When does the Orrery Room close, and can I get there without stairs?"*
  scores 0.8 on context precision with four sections (retrieved: The Orrery Room,
  Step-free access, Opening hours, The Whitby Orrery; answer: closes at 17:00,
  reachable by the East Wing lift). With one section it scores 0.4: only "The
  Orrery Room" came back, and the answer was "The Orrery Room closes thirty
  minutes before the rest of the museum. I don't know if you can get there
  without stairs."
- *"What time is the Whitby Orrery wound, and which room is it in?"* drops from
  0.8 to 0.6 with one section.

The other column is the surprise: hallucination stays at or near zero in both
runs. Starving retrieval did not make the model invent anything, it made it
honestly incomplete, and only the precision judge notices. Hallucination checks
the answer against the retrieved context, so a grounded-but-partial answer
passes it.

## Run it yourself

1. Install [uv](https://docs.astral.sh/uv/) and start a local Opik
   ([self-hosting guide](https://www.comet.com/docs/opik/self-host/local_deployment)),
   or use Opik Cloud.
2. `cp .env.example .env`, then fill in `OPENAI_API_KEY`. For Opik Cloud, replace
   `OPIK_URL_OVERRIDE` with your key and workspace as described in the file.
3. `uv sync`
4. `uv run main.py` (about a minute and under a cent of OpenAI usage).
5. Open the `langgraph-museum-guide-rag` project in Opik and follow the
   previous section.

Offline tests (no keys, no Opik needed):

```
env -u OPENAI_API_KEY -u ANTHROPIC_API_KEY OPIK_TRACK_DISABLE=true uv run pytest
```

`OPIK_TRACK_DISABLE=true` turns off all Opik logging; the traced functions run as
plain Python.

## Poke around

- In `main.py`, change the experiment list from `[(4, "k4-baseline"), (1, "k1-starved")]`
  to `[(4, "k4-baseline"), (8, "k8-flooded")]`. Does more context ever hurt the
  hallucination score, or only precision?
- Edit `data/visiting.md` so the Orrery Room closes at 16:30 but leave
  `data/galleries.md` alone. The two sections now disagree; check what the
  answer says and what the judges make of it.
- Add a question to `DATASET_ITEMS` in `guide/evaluation.py` that needs three
  sections at once (cafe hours, step-free access, and a ticket price) and compare
  how k = 2 and k = 4 cope.
- Tighten `SYSTEM_PROMPT` in `guide/graph.py` to require naming the guide section
  behind each claim, then rerun and check which experiment's rows change most.

## Gotchas we hit

**The `vector_search` span input contains `'store': '<langchain_core.vectorstores.in_memory.InMemoryVectorStore object at 0x...>'`.**
`@opik.track` logs every argument, and the vector store is passed in as one.
Exclude it: `@opik.track(name="vector_search", type="tool", ignore_arguments=["store"])`.
The span input is then just `question` and `k`.

**Run logs `Dataset 'museum-guide-questions' was found via workspace-wide search` and `The project_name parameter of evaluate() is deprecated`.**
With the 2.3 SDK, the dataset should belong to a project, and `evaluate()` takes
its project from the dataset. Create it with
`client.get_or_create_dataset(name=..., project_name=PROJECT_NAME)` and do not
pass `project_name` to `evaluate()`.

**A script that only reads from Opik prints `No project name configured. Traces are being logged to "Default Project"`.**
`OPIK_PROJECT_NAME` is read when the client is created, and `main.py` sets it
before importing anything from Opik. A separate verification script needs the
same variable (or `opik.Opik(project_name=...)`) or anything it logs lands in
the wrong project.

**Scores move between identical runs.**
`k4-baseline`'s context precision came out at 0.78, 0.84 and 0.76 across three
runs of the same code, because the judge is an LLM. Treat differences of a few
hundredths as noise; compare per-question rows, like the Orrery Room question
(0.8 versus 0.4), rather than the averages alone.

## How it's put together

- `main.py`: loads keys, sets the Opik project, runs the demo questions and the two experiments, flushes.
- `guide/corpus.py`: splits `data/*.md` into one chunk per `##` section.
- `guide/retrieval.py`: builds the in-memory vector store; `search()` is the traced `vector_search` tool span.
- `guide/graph.py`: the `State`, the prompt, and the retrieve-to-generate graph with the Opik tracer attached.
- `guide/evaluation.py`: the nine-question dataset, the `evaluate()` call, and the score summary.
- `data/`: the fictional Alderbank guide (galleries, visiting, accessibility, collection).
- `tests/test_guide.py`: offline tests with fake embeddings and a stub chat model, including a call to the traced `search()` with tracking disabled.
- `.env.example`, `pyproject.toml`, `.python-version`: configuration and the pinned toolchain.

---

*built with Opik · inspired by Opik's examples and documentation*
