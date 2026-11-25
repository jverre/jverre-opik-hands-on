# mastra-library-holds-agent

*A public-library desk agent that renews, reserves and collects fines, and leaves a readable tool-call tree behind in Opik.*

![Node 22.13+](https://img.shields.io/badge/node-22.13%2B-339933?logo=node.js&logoColor=white)
![Mastra core 1.86](https://img.shields.io/badge/%40mastra%2Fcore-1.86-0b0b0b)
![Opik via OTLP](https://img.shields.io/badge/Opik-OTLP%20ingest-2f54eb)

When a patron-facing agent says "I can't renew that, you owe a fine", you want to know whether the library's rules said so or the model made it up. A chat transcript can't tell you. An agent trace can: it records which tool the model chose, which arguments it passed, and what the tool returned. This project is a small desk assistant for the fictional Larkspur Public Library, built with [Mastra](https://mastra.ai/), where every patron request shows up in Opik as an agent loop with a real `execute_tool` span for each tool call.

## What you'll build

- Five tools (`search_catalogue`, `get_account`, `place_hold`, `renew_loan`, `pay_fine`) that wrap plain circulation rules over in-memory fictional data: 4 books, 2 patrons, a hold queue, one overdue loan.
- A `gpt-4o-mini` Mastra agent that must call a tool before talking about an account, and must report what the tool returned rather than deciding eligibility itself.
- A scripted demo of four requests: a clean renewal, a renewal refused because someone is waiting, a three-tool chain (search, hold, account check), and a renewal blocked by $12 of fines.
- Tracing as configuration: `src/observability.ts` is the only file that knows Opik exists.

## See it in Opik

Open the `mastra-library-holds-agent` project (local default: http://localhost:5173) and look at the Traces tab. After one demo run there are 4 traces, each named `invoke_agent larkspur-patron-agent`, with 22, 29, 22 and 15 spans (newest first, so the fines-blocked request is on top).

Open the 29-span trace, the search-hold-account request, and expand it. Under the root `invoke_agent` span there are four `agent_step` spans, one per model turn. Each holds a `chat gpt-4o-mini` span of type `llm` (4 in total) and, where the model chose a tool, an `execute_tool` span of type `tool`. This one has three: `execute_tool searchCatalogue` with input `{"query":"The Salt Road"}`, `execute_tool placeHold` with `{"patron_id":"P-3001","book_id":"B-100"}` and the output `{"ok":true,"hold_id":"H-902",... "queue_position":1}`, and `execute_tool getAccount`. The run has 8 `execute_tool` spans across the four traces.

The refusals are the interesting rows. In the 22-span trace for L-502, `execute_tool renewLoan` returns `ok: false` with the error "cannot be renewed: another patron is waiting for it", which proves the refusal came from the library rules. The trace-level Usage and Cost columns are filled: that same trace shows 1,821 tokens in total (1,733 prompt) and roughly $0.0003; the whole run costs around $0.0014.

You will also see span noise: `processor_run`, `model_chunk` and `model_generation` spans (type `general`) sit alongside the useful ones. Filter the span list by type `tool` to see only the tool calls.

## Run it yourself

1. Start a local Opik ([self-hosting guide](https://www.comet.com/docs/opik/self-host/local_deployment)), or use Opik Cloud.
2. `cp .env.example .env` and set `OPENAI_API_KEY` (a repo-root `.env` also works). For Opik Cloud set `OPIK_API_KEY` and `OPIK_URL_OVERRIDE=https://www.comet.com/opik/api`.
3. `npm install`
4. `npm run demo` (about 20 seconds)
5. Open the `mastra-library-holds-agent` project in Opik and click the newest trace.

Offline checks need no keys and no Opik: `npm test` and `npm run typecheck`.

## Poke around

- Raise `FINES_BLOCK_USD` in `src/library/rules.ts` to 20 and rerun: request 4 now succeeds, and the `renewLoan` span output flips to `ok: true` with no prompt change.
- Delete the "never decide eligibility yourself" sentences from `src/agents/patronAgent.ts` and rerun. Watch for traces where the agent refuses a renewal without any `renewLoan` span at all.
- Add a fifth request such as "I'd like to pay $5 on my fine, card P-3002" and see `pay_fine` slot into the loop, then follow it with a renewal request in the same run to watch state carry over (it is shared in memory).
- Set `maxSteps: 2` in `src/demo.ts` and look at how the multi-tool request gets cut off.

## Gotchas we hit

- **Symptom:** the demo runs fine, but no `mastra-library-holds-agent` project ever appears in Opik, and nothing errors. **Cause:** with `protocol: "http/json"` the exporter's requests never produced traces against a local Opik (a hand-written JSON POST to the same endpoint simply hung). **Fix:** use protobuf and install its exporter: `npm i @opentelemetry/exporter-trace-otlp-proto` and set `protocol: "http/protobuf"` in the `OtelExporter` custom provider.
- **Symptom:** traces land in the wrong project, or `Default Project`. **Cause:** Opik picks the project from the OTLP `projectName` header. **Fix:** `headers: { "Comet-Workspace": "default", projectName: "mastra-library-holds-agent" }`; send `Authorization` only for Opik Cloud.
- **Symptom:** the trace-level Output column is empty even though the agent answered. **Cause:** Mastra's span-to-OTel mapping puts the answer on child spans, not on the root. **Fix:** read the answer from the last `chat gpt-4o-mini` span; this example doesn't add a mapper.
- **Symptom:** the agent tells a patron they can't renew because of a $3.50 fine, and the trace has no `renewLoan` span. **Cause:** the model invented a rule instead of calling the tool. **Fix:** say in the instructions that tools enforce the rules and that small balances are not a reason to skip them (see `src/agents/patronAgent.ts`); the trace is how you spot it.

## How it's put together

- `src/data/catalogue.ts`: fictional books, patrons, loans and holds, plus a fixed "today" so runs repeat.
- `src/library/rules.ts`: the circulation rules (renewal limits, hold queue, fines block) as plain functions.
- `src/library/state.ts`: the shared mutable library the tools act on, with a reset.
- `src/tools/index.ts`: the five Mastra tools, thin wrappers over the rules.
- `src/agents/patronAgent.ts`: the agent's instructions, model and tool list.
- `src/observability.ts`: the Opik OTLP exporter and project routing.
- `src/mastra.ts`: the Mastra instance that registers the agent and observability.
- `src/demo.ts`: loads env, runs the four scripted requests, flushes the exporter.
- `tests/rules.test.ts`, `tests/tools.test.ts`: offline tests of the rules and of tool `execute()` without any exporter or model.

Tracing is only built when `src/mastra.ts` is imported, and the tests never import it, so they need no Opik and no keys.

---

*built with Opik · inspired by Opik's examples and documentation*
