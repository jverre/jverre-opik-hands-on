# openai-agents-insurance-claims

**A claims line where a triage agent hands customers to water, theft and storm specialists, and Opik shows who did what.**

![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![openai-agents 0.26](https://img.shields.io/badge/openai--agents-0.26-412991?style=flat)
![Opik 2.3](https://img.shields.io/badge/Opik-2.3-2f54eb?style=flat)

When a home-insurance customer gets a wrong answer ("yes, you are covered" for a flooded basement), the transcript alone cannot tell you which part of the system is to blame. Was the customer sent to the wrong specialist? Did the specialist skip the policy lookup? Did the lookup return an exclusion that the model talked past? This small app makes those questions answerable. It is a claims desk built on the OpenAI Agents SDK, traced with Opik, running against a fictional policy book.

## What you'll build

Four agents on `gpt-4o-mini`:

- **Claims Triage Agent** only routes. It has no tools, just three handoffs.
- **Water Damage Agent**, **Theft Agent** and **Storm Damage Agent** each own the shared tools `check_coverage`, `estimate_payout`, `open_claim` and `get_claim_status`, plus one tool of their own: `request_mitigation_crew`, `attach_police_report` or `book_adjuster`.

The policy and claim data live in `data/*.json` (three invented policyholders, two existing claims). All the business rules (limits, deductibles, the flood exclusion) are plain Python in `claims_desk.py`, so no insurance API and no extra key is needed beyond `OPENAI_API_KEY`.

`main.py` plays four scripted customers, seven turns in total:

| Thread | Customer says | What should happen |
| --- | --- | --- |
| `kitchen-pipe-burst` | Burst pipe, policy HP-4410, $6,200 | claim opened, then payout $5,700 and a crew dispatched |
| `garage-ebike-theft` | Stolen e-bike, policy HP-7302, $2,400 | claim opened, police report attached, payout $2,150 |
| `roof-shingles-storm` | Torn shingles, policy HP-2288, $9,000 | coverage explained, then a claim and an adjuster for Saturday |
| `basement-groundwater` | Rising groundwater, policy HP-2288, $12,000 | **refused**: flood is excluded, no claim is opened |

Opik is wired in with `set_trace_processors([OpikTracingProcessor()])` and each turn runs inside the SDK's `trace(..., group_id=...)` block.

## See it in Opik

Open the **`openai-agents-insurance-claims`** project. The Traces tab holds 7 traces named `Claims triage`, one per customer turn.

Open the first `kitchen-pipe-burst` trace and expand it. The root `Task` span has two children: first `Claims Triage Agent`, whose single `Turn` contains one `Response` llm span (247 tokens) and a `Handoff` span, then `Water Damage Agent`. The specialist's span has three turns. In the first, a `check_coverage` tool span shows the arguments the model chose (`{"policy_id":"HP-4410","peril":"sudden_water"}`) and the JSON the desk returned. The second turn calls `open_claim` and gets back `CL-4003`. The third writes the reply. In total that trace has 14 spans (4 llm, 2 tool, 8 general) and costs about $0.0004.

The most instructive trace is the `basement-groundwater` one. Its tool span, `check_coverage` with `"peril":"flood"`, returns `"covered": false` with the note about rising groundwater. The specialist never calls `open_claim`, and the trace has only one tool span. That is what a correct refusal looks like: the decision is visible in the tool result, not just asserted in the reply. If a future prompt change makes the agent open a claim anyway, you will see an `open_claim` span in this trace where there should be none.

Now open the **Threads** tab. There are four threads, one per customer (`kitchen-pipe-burst-<id>`, `garage-ebike-theft-<id>`, and so on). Three of them hold two traces, `basement-groundwater` holds one. Clicking a thread shows both turns in order, so "send a crew today" is read next to the claim that was opened a turn earlier. The thread id is just the `group_id` we passed to `trace()`.

The whole demo takes about 45 seconds and costs roughly $0.002 in total.

## Run it yourself

1. Start a local Opik (see the [self-hosting guide](https://www.comet.com/docs/opik/self-host/local_deployment)) or point the SDK at Opik Cloud.
2. `cp .env.example .env` and set `OPENAI_API_KEY`. For a local Opik also set `OPIK_URL_OVERRIDE=http://localhost:5173/api/` and `OPIK_WORKSPACE=default`. The app also loads a `.env` one directory up, if you keep a shared one there.
3. `uv sync`
4. `uv run main.py`
5. `uv run verify.py` reads the project back through the SDK and prints trace counts, threads, span types, tokens and cost per trace. Open `http://localhost:5173` and look at the `openai-agents-insurance-claims` project.

## Poke around

- Remove "If water arrived because of a storm, choose the water specialist." from the triage instructions, then send "a tree fell on the roof and rain is pouring into the attic". Compare which specialist the `Handoff` span lands on before and after.
- Delete the `check_coverage` instruction from `COMMON_RULES` in `claims_agents.py` and rerun the groundwater customer. Does the agent still avoid `open_claim`? Opik will tell you.
- Give the Storm Damage Agent a handoff back to triage and add a customer who starts with a storm claim and then reports a theft.
- Add a fourth specialist (say, liability) with its own tool. The new handoff shows up in traces without any tracing changes.

## Gotchas we hit

**Symptom:** the second turn of a conversation gets a vague reply such as "I have connected you with the water damage agent who will assist you", and the trace has no `estimate_payout` or `request_mitigation_crew` span.
**Cause:** the first version of the demo started every turn at `triage_agent`, so each follow-up was routed again from scratch and the customer's request ("send a crew", "what will I be paid") was answered by a reply that never called the tool.
**Fix:** keep the agent that took over and start the next turn from it:
```python
current_agent = result.last_agent   # then Runner.run_sync(current_agent, conversation_input)
```
As a result only the first trace of each thread contains a `Handoff` span.

**Symptom:** you filter spans by type for "handoffs" and get nothing.
**Cause:** the tracing processor logs handoffs as `general` spans named `Handoff`, and agent turns as `general` as well. Only LLM responses (`llm`) and function tools (`tool`) get their own span type.
**Fix:** filter by name (`name = Handoff`) or, in code, `s.name.startswith("Handoff")` as `verify.py` does.

## How it's put together

- `main.py` — the demo: Opik setup, the four scripted customers, one `trace()` per turn, flush at exit.
- `claims_agents.py` — the function tools, the three specialists and the triage agent.
- `claims_desk.py` — policy lookup, payout maths, claim lifecycle; pure Python, no model calls.
- `data/policies.json`, `data/claims.json` — the fictional policy book and existing claims.
- `verify.py` — reads the project back from Opik and prints a summary.
- `tests/` — offline tests for the desk rules, the agent wiring, and a traced function with tracking disabled. Run with `env -u OPENAI_API_KEY OPIK_TRACK_DISABLE=true uv run pytest`.

*built with Opik · inspired by Opik's examples and documentation*
