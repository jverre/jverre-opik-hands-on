# temporal-py-grant-review

**Grant applications reviewed by a durable workflow, traced as one story across the client and the worker.**

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![Temporal](https://img.shields.io/badge/temporalio-1.37-000000?style=flat)
![OpenAI](https://img.shields.io/badge/model-gpt--4o--mini-412991?style=flat&logo=openai&logoColor=white)
[![Opik](https://img.shields.io/badge/Opik-OTLP_ingestion-2f54eb?style=flat)](https://github.com/comet-ml/opik)

## The problem

A fictional small-grants fund, the Harbor Lane Community Fund, screens applications in three steps: an LLM checks eligibility against the fund's rules, plain code checks that the budget adds up, and an LLM writes a short briefing for the human reviewer. Run that on Temporal and each step becomes a retried, persisted activity. That also means two operating-system processes touch one review: the one that starts the workflow and the worker that runs it. Ordinary tracing gives you two disconnected halves. This example puts them back together in Opik, including the step that fails and is retried.

## What you'll build

- A `GrantReview` workflow with three activities: `check_eligibility` (gpt-4o-mini, JSON output), `check_budget` (pure Python, and it raises a "Finance ledger service unavailable (503)" error on its first attempt of every run), and `write_reviewer_summary` (gpt-4o-mini).
- Three invented applications in `data/applications.json`: a clean one (`GR-101`), one whose budget lines sum to 4,300 against a 4,800 request (`GR-102`), and one from the wrong county that also breaks the 5,000 cap and plans out-of-county travel (`GR-103`).
- A demo that starts a local Temporal dev server from Python, runs the worker as a separate process, reviews the three applications, and shuts everything down.
- Tracing with Temporal's own OpenTelemetry interceptor (`temporalio.contrib.opentelemetry.TracingInterceptor`) in both processes, exported over OTLP to Opik. There is no Opik-specific Temporal package for Python here, so the OTLP route is the integration, plus hand-written `gen_ai.*` attributes on the LLM spans.

## See it in Opik

Open the `temporal-py-grant-review` project in the local Opik UI (`http://localhost:5173` by default). After a run it lists three traces, `review:GR-101`, `review:GR-102` and `review:GR-103`, each costing roughly $0.0001 to $0.00016.

Open any of them. The span tree has 13 spans under one root. `review:GR-10x` and `StartWorkflow:GrantReview` were created by the client process. `RunWorkflow:GrantReview`, the `StartActivity` and `RunActivity` spans and the LLM calls were created by the worker, and they sit in the same tree because the interceptor carries the trace context through Temporal's headers.

Look at the budget step. There are two `RunActivity:check_budget` spans: the first is marked as an error with "Finance ledger service unavailable (503)", the second is clean. Between them sits Temporal's retry, about a second later. The two `llm`-type spans, `eligibility-check` and `reviewer-summary`, carry the full prompt, the JSON or text reply, model `gpt-4o-mini-2024-07-18`, and token counts that Opik prices into the trace cost. Filter the Spans tab by errors and you will see exactly three red spans, one per review.

## Run it yourself

1. Have a local Opik running (`http://localhost:5173`) and an OpenAI key.
2. `cp .env.example .env` and fill in `OPENAI_API_KEY` (a `.env` further up the tree is found too).
3. `uv sync`
4. `uv run grant-demo` (about 25 seconds; the first run also downloads the Temporal dev server binary).
5. `uv run grant-check` reads the traces back through the Opik SDK and prints, per trace, the span count, cost, number of `check_budget` attempts and the failed attempt's error message. It exits non-zero if any trace is not one tree with exactly one failed attempt.
6. Offline tests: `env -u OPENAI_API_KEY OPIK_TRACK_DISABLE=true uv run pytest`.

For Opik Cloud set `OPIK_URL_OVERRIDE`, `OPIK_WORKSPACE` and `OPIK_API_KEY`; the OTLP URL is derived from the same variables, or set `OTEL_EXPORTER_OTLP_ENDPOINT` directly.

## Poke around

- In `grant_review/activities.py` change `attempt == 1` to `attempt <= 2` (the retry policy allows three attempts): the trace now has three `RunActivity:check_budget` spans, two red.
- Make it fail past the limit (`attempt <= 3`) and watch the workflow give up with an error instead of a summary.
- Edit `data/grant_rules.md` (say the cap is 3,000) and compare the `eligibility-check` span's JSON output for `GR-101`.
- Remove the `TracingInterceptor` from only the worker's `Client.connect` and rerun: the worker no longer reads the client's trace context, so its spans stop joining the client's trace.

## Gotchas we hit

- **The retried activity floods the terminal with a `RuntimeError` traceback.** That is Temporal logging the deliberate first-attempt failure, not a crash. The run still exits 0 and the next attempt succeeds.
- **`RunWorkflow:GrantReview`, `StartActivity` and `CompleteWorkflow` show a 0 ms duration.** Temporal creates workflow-side spans replay-safely, as instant markers, so only `RunActivity` spans and the LLM spans measure real time. Read timing from those.
- **`uv sync` fails with "Readme file does not exist: README.md".** `pyproject.toml` declares `readme = "README.md"` and hatchling refuses to build the editable install without it. Keep the file next to `pyproject.toml`, or drop the `readme` line.

## How it's put together

- `grant_review/workflows.py` — the `GrantReview` workflow and its retry policy.
- `grant_review/activities.py` — the three activities, including the deliberate first-attempt failure.
- `grant_review/llm.py` — OpenAI calls, each wrapped in an LLM span.
- `grant_review/tracing.py` — OTLP exporter for Opik, the Temporal tracing interceptor, and the `gen_ai.*` span helper.
- `grant_review/worker.py` — the worker process; flushes spans on SIGTERM.
- `grant_review/demo.py` — dev server, worker subprocess, three reviews.
- `grant_review/check_trace.py` — reads the traces back from Opik and checks the cross-process shape.
- `grant_review/budget.py`, `grant_review/config.py` — the deterministic budget check; settings and data loading.
- `data/` — the fictional applications and the fund's rules.
- `tests/test_grant_review.py` — offline tests for the budget logic, the OTLP URL, trace summarising and a stubbed model call.

---

*built with Opik · inspired by Opik's examples and documentation*
