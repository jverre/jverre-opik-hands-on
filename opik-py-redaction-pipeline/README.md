# opik-py-redaction-pipeline

**Redact personal data from documents in four steps, and watch every step show up in Opik as a span you wrote yourself.**

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![Opik](https://img.shields.io/badge/opik-2.3.3-2f54eb?style=flat)
![OpenAI](https://img.shields.io/badge/model-gpt--4o--mini-412991?style=flat&logo=openai&logoColor=white)

Before you let documents leave a system, you scrub them: names, emails, card numbers, birth dates. A redactor that only uses a model will sometimes miss something, and a redactor that only uses patterns will miss everything that isn't a pattern. The hard part is not writing the redactor. It is *knowing, per document, whether it worked*. This example builds a small pipeline and traces it with nothing but the low-level Opik client, so the trace tree, the token usage, the cost, and the pass/fail verdict are all things you put there deliberately.

## What you'll build

A script that pushes five made-up documents (a support ticket, an HR note, a clinic intake form, an invoice reminder, and a meeting note with no personal data at all) through:

```
document -> trace "redact-document"
  |- detect    (general)    groups the two detectors
  |   |- regex-scan (tool)  emails, phones, SSNs, card numbers
  |   `- chat gpt-4o-mini (llm)  names, addresses, birth dates, member IDs
  |- classify  (general)    merge, drop hallucinated strings, tag category + severity
  |- redact    (tool)       swap each entity for [PERSON_1], [EMAIL_1], ...
  `- audit     (guardrail)  does any detected or planted string survive in the output?
trace feedback scores: leak_free, recall, precision
```

There are no decorators and no OpenAI wrapper. The OpenAI call is the plain SDK; the code then copies the model name, provider and token counts onto the `llm` span by hand, which is exactly what lets Opik compute its dollar cost.

## See it in Opik

Open the `opik-py-redaction-pipeline` project (local stack: <http://localhost:5173>). The Traces tab holds five `redact-document` traces, each tagged with its document id and each carrying three feedback score columns: `leak_free`, `recall` and `precision`. Four of them score 1.0 across the board. Sort or filter on `leak_free` and the odd one out is `support-ticket-1042`: `leak_free` 0.0, `recall` 0.8.

Open that trace. The tree has six spans: `detect` with `regex-scan` and `chat gpt-4o-mini` under it, then `classify`, `redact` and `audit`. The `audit` guardrail span shows the reason for the failure in its output: the string `Marisol` is still in the redacted text. The ticket names Marisol Venkataraman once in full and then says "please tell Marisol" at the end. The model tagged the full name and missed the lone first name, so the output reads `[PERSON_1] wrote in ... please tell Marisol the lid is covered`. Without the audit step you would have shipped it. (The model is non-deterministic, so a rerun may catch the first name. The audit will say so either way.)

Each `chat gpt-4o-mini` span has the exact messages that were sent, the JSON the model returned, a model of `gpt-4o-mini-2024-07-18`, and usage such as 170 prompt and 118 completion tokens for the support ticket. The cost column on that span is about $0.0001, computed by the server. The whole run of five documents costs under $0.001.

## Run it yourself

1. Install [uv](https://docs.astral.sh/uv/) and start a local Opik, or use Opik Cloud.
2. `cp .env.example .env`, then fill in `OPENAI_API_KEY`. For Opik Cloud, set `OPIK_API_KEY` and `OPIK_WORKSPACE` and remove `OPIK_URL_OVERRIDE`.
3. `uv run main.py` (about 20 seconds; it prints each redacted document and a final score line).
4. Open the project in Opik and look at the Traces tab.

Tests need no keys and no Opik: `env -u OPENAI_API_KEY OPIK_TRACK_DISABLE=true uv run pytest`.

## Poke around

- Delete the `usage={...}` argument on the `chat gpt-4o-mini` span and run again. The span still appears with its messages, but its cost is empty.
- Add a line to `data/documents.json` with a sneaky identifier (a nickname, a passport number) and see which detector catches it, and what `recall` says when neither does.
- In `audit`, nothing blocks the output when a leak is found. Make `process_document` raise on `leak_free == False` and see how the trace looks with an error.
- Swap `MODEL` in `pipeline.py` for `gpt-4.1-mini` and compare the cost and the `Marisol` outcome across the two runs.

## Gotchas we hit

**"OPIK: Calling Span.end() shortly after creation with batching enabled may cause data loss."** One warning per span and trace. Cause: opening a span, doing work, then calling `.end()` produces an update that can overtake the batched create. Fix: do the work first, time it yourself, then create each span in a single call that already has its result:

```python
trace.span(name="redact", type="tool", input=..., output=...,
           start_time=t0, end_time=t1)
```

**The `cost` column is empty on a span you traced by hand.** Cause: Opik prices a span from `model`, `provider` and `usage`; a bare `type="llm"` span has none of them. Fix: pass `model=response.model`, `provider="openai"` and `usage={"prompt_tokens": ..., "completion_tokens": ..., "total_tokens": ...}` when you create the span.

**Traces vanish when a script is killed.** Spans are sent from a background thread. A normal exit flushes via an `atexit` hook (we confirmed a script with no flush still delivered), but `os._exit()`, a crash or a killed worker skips it and the batch is lost. Fix: call `opik_client.flush()` at the end of the run, as `main.py` does.

## How it's put together

- `main.py` loads the fixtures, creates the `opik.Opik` client, runs each document and flushes.
- `pipeline.py` holds the pure steps (scan, parse, merge, classify, redact, audit) and `process_document`, which times them and writes the trace, spans and feedback scores.
- `data/documents.json` has the five fictional documents and the personal data planted in each, used by the audit and the scores.
- `tests/test_pipeline.py` covers the parsers, merge, redaction order, the audit, and runs the traced pipeline with a stubbed model and tracking disabled.
- `.env.example` lists the variables; `pyproject.toml` pins `opik==2.3.3`.

---

*built with Opik · inspired by Opik's examples and documentation*
