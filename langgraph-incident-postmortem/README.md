# langgraph-incident-postmortem

*Three LangGraph agents write a blameless post-mortem from raw alerts, logs and chat, and Opik shows you the whole investigation, loop included, as one trace.*

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![LangGraph](https://img.shields.io/badge/langgraph-1.2-1C3C3C?style=flat)
![Opik](https://img.shields.io/badge/opik-2.3-2f54eb?style=flat)

After an outage, someone has to turn a pile of pager alerts, log excerpts and chat scrollback into a readable post-mortem. An agent team can do the first draft, but when the draft blames the wrong thing or skips a timestamp you need to know which step went wrong: the plan, one of the evidence passes, or the final write-up. This example gives you a small team you can open up and inspect.

## What you'll build

A LangGraph graph with a genuine loop, running `gpt-4o-mini` throughout:

```
planner --> investigator --+
                ^          |  open inquiries left? loop
                +----------+  all answered? --> writer --> post-mortem
```

- The **planner** uses structured output to split the incident ("the invoice API errored for about 50 minutes on 3 March") into 3 to 4 lines of inquiry: timeline, trigger, response, process gaps.
- The **investigator** answers one inquiry per pass. It searches `data/`, an offline corpus of fictional Ledgerly evidence (pager alerts, service logs, chat excerpts, release notes, a runbook), with a rarity-weighted keyword search. No web, no vector database.
- A conditional edge sends it around again until every inquiry has a finding, then the **writer** drafts a post-mortem with Summary, Impact, Timeline, Contributing factors, What went well and Action items, blameless by instruction.

## See it in Opik

Run it, then open the **`langgraph-incident-postmortem`** project in Opik (http://localhost:5173 for a local install) and click the one trace named `LangGraph`.

In my verified run the trace held 23 spans. The top-level spans are the agents in execution order: `planner`, four `investigator` passes, `writer`, plus a small `route_investigation` span after each investigator pass recording the loop decision. Open an `investigator` span and you see two children: a `search_corpus` span of type `tool` (the query in, the three matched log or chat sections out, so you can tell whether a wrong claim came from retrieval or from the model) and a `ChatOpenAI` llm span with the exact prompt, completion and token counts. Switch the trace to its agent graph view and you get the planner, the investigator with its arrow back to itself, and the writer.

Cost per agent falls out of the llm spans, which carry model `gpt-4o-mini-2024-07-18`, token usage and an estimated cost. Summing each agent's llm span: planner about $0.00008, the four investigator passes about $0.00054, writer about $0.00046, for $0.00108 and 3,579 tokens in total. The writer costs nearly as much as all the investigation, and one more inquiry from the planner would add a whole extra investigator pass; the trace shows both effects without any extra bookkeeping.

## Run it yourself

1. Have Opik running (`opik.sh` for a local stack, or point at Opik Cloud) and an OpenAI key.
2. `cp .env.example .env`, fill in `OPENAI_API_KEY`, and adjust the Opik lines if you aren't on the local default `http://localhost:5173/api/`. The script also reads a `.env` one directory up.
3. `uv sync`
4. `uv run main.py` (takes a few seconds and costs roughly a tenth of a cent)
5. Open the project in Opik as described above.

Offline tests, no keys and no Opik needed:

```
OPIK_TRACK_DISABLE=true uv run pytest
```

## Poke around

- Edit `INCIDENT` in `main.py` to something the evidence only half covers ("why did the status page update late?") and read the investigator findings: they should say what the files don't contain.
- Change the planner prompt to demand exactly two inquiries. The trace loses two investigator passes and the cost drops accordingly.
- Open `data/deploy-notes.md` and change the retry change to something harmless, then see whether the writer's "Contributing factors" follows the evidence or invents a cause. Click through the `search_corpus` span to see what it was fed.
- Swap `MODEL` for another model and compare the per-agent cost split.

## Gotchas we hit

- **`openai.OpenAIError: Missing credentials` when you import the module or run the tests.** `ChatOpenAI(...)` raises as soon as it is constructed without a key, so a module-level `llm = ChatOpenAI(...)` makes every unit test need a key. Fix: build it lazily, as `main.py` does with `@functools.cache def get_llm()`, and monkeypatch `main.get_llm` in tests.
- **The planner's llm span is not a direct child of `planner`.** With structured output the model call runs inside a `RunnableSequence` (plus small `RunnableLambda` and `_check_refusal` spans), so you open `planner` then `RunnableSequence` to reach the `ChatOpenAI` span. Investigator and writer, which call the model directly, have it one level down. Cost per agent still adds up correctly if you sum all llm spans under each node.
- **`search_corpus` shows as a tool span only inside a node.** It is wrapped with `@opik.track(type="tool")`, and in my run it nested under each `investigator` span because it is called from inside the node function. Remove the decorator and the retrieval step vanishes from the trace, leaving only the model call.

## How it's put together

- `main.py`: corpus loader and search (a tracked tool), the three agents, the graph, and the Opik wiring.
- `data/`: five fictional evidence files (`alerts.md`, `service-logs.md`, `chat-excerpts.md`, `deploy-notes.md`, `runbook.md`).
- `tests/test_postmortem.py`: offline tests with a stubbed model for search, routing, the investigator, note formatting and the full graph.
- `tests/conftest.py`: puts the project folder on the import path.
- `pyproject.toml`, `.env.example`, `.gitignore`: dependencies (uv, Python 3.12+), the env template, ignored files.

---

*built with Opik · inspired by Opik's examples and documentation*
