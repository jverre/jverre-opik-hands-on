<div align="center">

# Marigold Lane Festival Planner

**`crewai-street-festival-planner`**

*Three CrewAI agents plan a street festival. Opik tells you which one spent the money.*

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![CrewAI](https://img.shields.io/badge/crewai-1.15%2B-FF5A50?style=flat)
[![Opik](https://img.shields.io/badge/Opik-2.3-2f54eb?style=flat)](https://github.com/comet-ml/opik)

</div>

A crew of agents hands you one finished answer. It does not tell you which agent produced which part, what each was given, or which one used most of the tokens. This example plans a fictional neighbourhood festival with three agents, records the whole run as a single Opik trace, and then reads the trace back to print tokens and dollars per agent.

## What you'll build

A `festival` command line tool, packaged under `src/street_festival/`, that runs a sequential CrewAI crew on `gpt-4o-mini`:

1. **Logistics Planner** sets marshal and toilet counts from the permit rules.
2. **Vendor Coordinator** places 15 vendors into four zones without exceeding each zone's amps.
3. **Budget Writer** turns both outputs into a budget against a $14,000 cap.

Everything the agents read lives in `data/` (a site description, a vendor quote sheet, and city permit notes), so the run is offline apart from the model calls. The vendor quotes add up to $13,450, which together with the required 8% reserve ($1,120) breaks the cap, so a good plan has to notice an overspend.

Two commands:

- `festival plan` runs the crew once.
- `festival costs` fetches the newest trace from Opik and totals tokens and cost per agent.

## See it in Opik

Open the `crewai-street-festival-planner` project. After one `festival plan` there is exactly one trace, named `kickoff`. In the run this README was written from it had 49 spans, 4,219 tokens (2,899 prompt, 1,320 completion) and an estimated cost of $0.0012.

Expand the tree. Under `kickoff` there are three `general` spans, `Task: Plan the site layout`, `Task: Place the vendors` and `Task: Write the budget`. Each holds one span named after its agent (`Logistics Planner`, `Vendor Coordinator`, `Budget Writer`), and inside that CrewAI's own planning flow. The money is on the `llm` spans called `chat_completion_create`, which carry the model (`gpt-4o-mini-2024-07-18`), token usage and cost. The agent spans themselves show no cost; the trace row shows the sum.

`festival costs` does the grouping for you:

```
agent                task                   calls  prompt  compl.  cost (USD)
Budget Writer        Write the budget           1    1217     250    0.000333
Vendor Coordinator   Place the vendors          1    1214     687    0.000594
Logistics Planner    Plan the site layout       1     468     383    0.000300
total                                           3    2899    1320    0.001227
```

The vendor coordinator is the most expensive agent because it writes the longest answer and reads the whole vendor sheet. The total matches the trace's cost column.

The same trace also shows a quality problem: in that run the budget writer reported a total of $8,900 although the vendor quotes alone are $13,450. Open the Budget Writer's llm span and compare its input with its output to see where the numbers were lost.

## Run it yourself

1. `cp .env.example .env` and add `OPENAI_API_KEY` (or keep a `.env` in a parent folder; the CLI walks up to find one).
2. Start a local Opik (https://www.comet.com/docs/opik/self-host/local_deployment). The defaults in `.env.example` point at `http://localhost:5173/api/`; the UI is at `http://localhost:5173`.
3. `uv sync`
4. `uv run festival plan` (about three minutes; a few hundredths of a cent of model cost)
5. `uv run festival costs`
6. Open the project in Opik and expand the newest trace.

Run the tests (no keys, no Opik needed): `env -u OPENAI_API_KEY OPIK_TRACK_DISABLE=true uv run pytest`

## Poke around

- Edit `data/vendors.csv` so the quotes fit under the cap and see whether the budget writer's total follows.
- Add `--verbose` to `festival plan` to watch the agents work while the trace is being recorded.
- Change `MODEL` in `src/street_festival/crew.py` for only the Budget Writer and compare `festival costs` across two runs.
- Add a fourth agent and task to `build_crew` and watch another `Task:` branch appear with no Opik changes.

## Gotchas we hit

- **The agent spans have no cost, only the `llm` spans do.** Cost and tokens are attached to each `chat_completion_create` span, which sits several levels below the agent (under CrewAI's `Flow.kickoff_async`). To total per agent, walk each llm span's parents up to the span directly under a `Task:` span, as `cost_by_agent` in `src/street_festival/costs.py` does.
- **Usage has extra keys.** Each llm span's `usage` holds `prompt_tokens`, `completion_tokens` and `total_tokens` plus many `original_usage.*` entries. Sum the first three; the others are the provider's raw breakdown.
- **Pass the crew to the tracker.** `track_crewai(project_name=..., crew=crew)` documents that on CrewAI 1.x the `crew` argument is needed so its LLM clients are patched; we always pass it and never ran without it.
- **Flush before exit.** The CLI calls `opik.flush_tracker()` in a `finally` block so a short-lived process still uploads its trace.

## How it's put together

- `src/street_festival/cli.py` - the `festival` entry point (`plan`, `costs`) and `.env` discovery.
- `src/street_festival/crew.py` - the three agents, three sequential tasks and the crew.
- `src/street_festival/data.py` - loads `data/` and renders it as prompt text.
- `src/street_festival/tracing.py` - the Opik project name, `track_crewai` call and flush.
- `src/street_festival/costs.py` - reads a trace's spans back and totals per agent.
- `data/site.json`, `data/vendors.csv`, `data/city_rules.md` - the fictional festival.
- `tests/test_data.py`, `tests/test_crew.py`, `tests/test_costs.py` - offline tests for the loaders, the crew wiring and the cost grouping, including one that enables tracing with tracking disabled.

---

*built with Opik · inspired by Opik's examples and documentation*
