# beeai-py-expense-approval

*A BeeAI ReAct agent that triages expense reports, with every thought, model call and tool call visible in Opik.*

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![BeeAI](https://img.shields.io/badge/beeai--framework-0.1.86-f5c518?style=flat)
![OpenInference](https://img.shields.io/badge/openinference--instrumentation--beeai-0.1.39-8a63d2?style=flat)

An agent that approves, bounces or rejects expense reports looks fine in a demo, because the final answer reads fluently. The trouble starts when it is *wrong* in a fluent way: it tells an employee their USD 18.50 taxi ride needs a receipt, and the only artifact you have is a confident paragraph. To fix that you need to see what the policy tool actually returned and what the model made of it.

This example reviews three expense reports for Harbor & Pine Outfitters, a fictional outdoor-gear retailer. The agent is a [BeeAI](https://framework.beeai.dev/) ReAct agent on `gpt-4o-mini`. It is traced with the OpenInference BeeAI instrumentation and an OTLP exporter pointed at Opik, so there is no Opik SDK in the agent code at all.

## What you'll build

- A ReAct agent with three tools over canned JSON in `data/`: `policy_lookup` (category limits and receipt thresholds), `receipt_check` (is a receipt on file for this report id?) and `manager_lookup` (who approves, and up to how much).
- Three scripted reports: a USD 342 client dinner (over the per-person meal cap, guest list missing), a USD 18.50 taxi ride with no receipt (under the USD 25 receipt threshold, so it should be fine), and a USD 1,240 airfare with no receipt (over the USD 800 no-pre-approval limit).
- A parser that turns the agent's `Decision / Reason / Approver / Message` answer into a typed verdict: `approve`, `needs_manager` or `reject`.
- `expense_agent/tracing.py`: the only file that knows about Opik. It sets up the OpenTelemetry tracer, the BeeAI instrumentation and the exporter.

## See it in Opik

Open the **`beeai-py-expense-approval`** project at `http://localhost:5173` (or your Opik Cloud workspace). After one run it holds **3 traces**, all named `ReAct`, one per expense report. Click one (the newest is the airfare report, ER-2043) and you will see **8 spans**: a root `ReAct` span of type *general*, with four `OpenAIChatModel` spans of type *llm* and three tool spans in between, in this order:

`ReAct` > `OpenAIChatModel` > `policy_lookup` > `OpenAIChatModel` > `receipt_check` > `OpenAIChatModel` > `manager_lookup` > `OpenAIChatModel`

- **The tool spans** hold the exact arguments (`{"category": "ground_transport"}`) and the exact JSON the tool returned. They are typed *general* rather than *tool* (see the gotchas).
- **The llm spans** show the full prompt, the model's `Thought:` or `Final Answer:` output, `gpt-4o-mini` as the model and `openai` as the provider. In my run the first and last model calls reported about 1.2k and 1.5k to 1.7k tokens, and the llm cost per trace came to between USD 0.0003 and USD 0.0005.
- **The root span's metadata** carries `iteration: 4` and an `iterations.N.thought / tool_name / tool_input / tool_output` entry for each loop turn. That is where the ReAct loop is summarised: the instrumentation does not emit a separate span per iteration, so look at the metadata, not the tree.
- **The failure to find:** open the ER-2042 trace (the taxi ride). The `policy_lookup` span returned `"receipt_required_over_usd": 25`, and the receipt span says no receipt is on file. The final answer says `needs_manager` with the reason "a receipt is required for expenses over USD 25, which is not provided", for an USD 18.50 fare. The tool data was right and the model drew the wrong conclusion: a prompt problem, not a data problem. In all of my runs this report was bounced to the manager.

## Run it yourself

1. Install [uv](https://docs.astral.sh/uv/) and start a local Opik (see the [Opik self-hosting guide](https://www.comet.com/docs/opik/self-host/local_deployment)), or use Opik Cloud.
2. `cp .env.example .env` and set `OPENAI_API_KEY` (an `.env` one folder up works too). For a local Opik nothing else is needed. For another Opik set `OPIK_URL_OVERRIDE` (default `http://localhost:5173/api/`), `OPIK_WORKSPACE` (default `default`) and, for Opik Cloud only, `OPIK_API_KEY`.
3. `uv run main.py` runs the three reports, which takes about 25 to 90 seconds and costs a few cents.
4. `uv run verify.py` reads the project back through the Opik SDK and prints each trace's report id, verdict, span order, per-call token counts and cost. (It uses the Opik SDK, so it needs your Opik config.)
5. Open the project in Opik and click a trace.
6. Run the offline tests with `uv run pytest`. They need no keys. If you have the Opik SDK configured, `OPIK_TRACK_DISABLE=true` keeps it quiet.

## Poke around

- Reword the taxi ride to USD 28 and watch `needs_manager` become the *right* answer: the receipt rule really does apply above USD 25.
- Add a stricter line to `INSTRUCTIONS` in `expense_agent/agent.py` ("a receipt is only needed when the amount is strictly over the threshold") and see whether ER-2042 flips to `approve`. Compare the new `policy_lookup` and final llm spans against the old trace.
- Add a `software` report (a USD 40 note-taking subscription). The policy says software never goes through expenses, so `reject` is what you should see; check what the `policy_lookup` span returned.
- Swap the model in `build_agent()` for another one BeeAI supports and compare the llm spans (model name, tokens, cost) across the same three reports.

## Gotchas we hit

1. **Symptom: every trace has about 190 extra spans named `new_token`, and the span count is in the hundreds.** BeeAI streams each model call and the instrumentation turns each streamed chunk into its own span. `OpikSpanCleaner` in `expense_agent/tracing.py` wraps the OTLP exporter and drops them (`[s for s in spans if s.name != "new_token"]`); the llm span still holds the complete output.
2. **Symptom: llm spans show token usage but cost is empty (`total_estimated_cost` is null).** BeeAI sets `llm.provider="openai"`, but Opik looks for the provider in `gen_ai.system`. The same exporter wrapper copies it across (`{**span.attributes, "gen_ai.system": span.attributes["llm.provider"]}`), after which Opik prices the span from the provider and model.
3. **Symptom: some `OpenAIChatModel` spans report `0` tokens** (typically the second and third of the four calls). The instrumentation itself records `usage.total_tokens: 0` for those streamed calls, so the sum of llm usage in a trace under-counts what you were billed for. Treat per-trace token totals as a lower bound.
4. **Symptom: tool calls show as `general` spans and there are no `iteration` spans.** The Python instrumentation maps its tool spans to Opik's *general* type, and the ReAct loop is summarised in the root span's metadata instead of child spans. Filter by span name (`policy_lookup`, `receipt_check`, `manager_lookup`) rather than by the `tool` type.

## How it's put together

- `main.py` loads the env, sets up tracing, runs the three reports and flushes the exporter.
- `expense_agent/agent.py` has the instructions, the `ReActAgent` on `gpt-4o-mini` and `review_report`.
- `expense_agent/tools.py` has the three tools, each a thin `@tool` wrapper over a plain function.
- `expense_agent/decision.py` parses the agent's final text into a `Decision`.
- `expense_agent/data.py` loads the JSON files in `data/` (policy, employees and managers, receipts, the three reports).
- `expense_agent/tracing.py` is the Opik wiring: exporter, headers, span cleaner, BeeAI instrumentation, flush.
- `verify.py` queries the Opik project and prints what the run produced.
- `tests/` has offline tests for the tools (including a tool run with no tracing configured), the decision parser and the tracing helpers.

---

*built with Opik · inspired by Opik's examples and documentation*
