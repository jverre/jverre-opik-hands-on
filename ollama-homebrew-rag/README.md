# ollama-homebrew-rag

*Ask a homebrewing handbook questions with zero cloud LLM calls, and still see exactly what the pipeline did.*

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![Ollama](https://img.shields.io/badge/ollama-llama3.2%3A1b-grey?style=flat)
![Opik](https://img.shields.io/badge/opik-2.3.3-2f54eb?style=flat)

A fully local RAG pipeline has no provider dashboard to fall back on. There is no request log at an API vendor and no usage page: if the 1B model gives a bad answer, the only record of why is whatever you traced yourself. This example runs a question-answering chain over a small fictional brewing handbook (the Copperkettle Handbook) with Ollama doing both the embedding and the answering, then shows how to get a trace that tells you whether a bad answer came from retrieval or from the model.

## What you'll build

- Four handbook files in `data/` (mashing, hop schedules, fermentation troubleshooting, sanitation), split into 16 chunks, one per `##` section.
- A LangChain chain: `nomic-embed-text` embeds the chunks into an in-memory vector store, the top 4 chunks go into a prompt, `llama3.2:1b` answers. Everything runs against a local Ollama server.
- `OpikTracer` on the chain, so each question becomes one trace. Because the tracer drops LangChain's retriever run, retrieval is wrapped in a function decorated with `@opik.track(type="tool")` so it still gets its own span.
- A deterministic `answer_has_fact` feedback score on each trace (does the answer contain the number or phrase the handbook gives?), so wrong answers sort to the top of the traces table.

Nothing here calls OpenAI, Anthropic or any other hosted model, and no provider key is read. Only the traces go to Opik, and a self-hosted Opik keeps those local too.

## See it in Opik

Open the `ollama-homebrew-rag` project. After one run it holds 4 traces, all named `ask_the_handbook`, tagged `ollama` and `local`, each lasting roughly 3 to 6 seconds on a laptop CPU. The traces table has an `answer_has_fact` column: three traces read 1.0 and one reads 0.0.

Click the 0.0 trace, the one for "How should I add hops for a hazy IPA whirlpool?". Its tree has a `search_handbook` span, shown with the tool icon, under a `retrieve` span. Its metadata says `k: 4` and lists the four sections it fetched, with `hops.md / Whirlpool hops` first. So retrieval did its job; the model was handed the right section (cool to 80 C, stir 20 minutes) and answered "add the hops 20 minutes after the boil is complete" anyway. Further down, the `ChatOllama` span is an `llm` span with the full prompt and answer, and `ls_model_name: llama3.2:1b` in its metadata.

Open any of the other three and the `search_handbook` span lists sections from the matching handbook file in the same way (for the sanitizer question, `sanitation.md / Sanitizer contact time` is first). The `ChatOllama` spans carry no token counts and no cost: `opik` has no usage extractor for Ollama, and there is nothing to bill anyway.

## Run it yourself

You need [uv](https://docs.astral.sh/uv/), a running Opik (the local default is `http://localhost:5173`), and an Ollama server with two small models. If you have no Ollama yet, `docker-compose.yml` starts one.

1. Start Ollama and pull the models (skip if you already have them):
   ```bash
   docker compose up -d
   docker compose exec ollama ollama pull llama3.2:1b
   docker compose exec ollama ollama pull nomic-embed-text
   ```
2. Point the SDK at your Opik and Ollama: copy `.env.example` to `.env` (or use a repo-root `.env`). No API key is needed for a local Opik.
3. Install: `uv sync`
4. Run: `uv run main.py` (under a minute on CPU for the four questions).
5. Open `http://localhost:5173`, then the `ollama-homebrew-rag` project.
6. Run the offline tests: `uv run pytest`

## Poke around

- Add "Who founded Copperkettle?" to `CASES` in `checks.py` with any `expected_fact`. The handbook doesn't say, so see which sections `search_handbook` returns and whether the 1B model admits it doesn't know.
- Change `TOP_K` in `rag.py` from 4 to 1 and re-run. The whirlpool answer may improve because the prompt shrinks, or another one may break because its section fell out of the top 1; the span metadata tells you which.
- Swap `CHAT_MODEL` to `llama3.2:3b` (after pulling it) and compare the 0.0 trace against the new one.
- Edit the mash temperature in `data/mashing.md` from 63 C to 64 C, update the case in `checks.py`, and confirm the new number shows up in the `search_handbook` span before it shows up in the answer.

## Gotchas we hit

**The retrieval step is missing from the trace.** The tree jumps from the question straight to the prompt, with no span for the vector search. Cause: in `opik` 2.3.3 with `langchain-core` 1.8.4, `OpikTracer` does not record the `VectorStoreRetriever` run when the retriever is a step in the chain. Fix: wrap retrieval in a named function and decorate it, then call that from the chain:

```python
@opik.track(name="search_handbook", type="tool")
def search_handbook(question: str) -> dict:
    docs = retriever.invoke(question)
    ...
```

**`usage` and cost are empty on the `ChatOllama` span.** Cause: `opik` 2.3.3 ships usage extractors for OpenAI, Anthropic, Bedrock, Google, Groq and Vertex AI, but none for Ollama, so no token counts are recorded and no cost can be computed. Nothing to fix here: for a local model the lesson is the trace, and cost is zero by construction. Filter by the `ls_model_name` metadata field when you want per-model comparisons.

## How it's put together

- `main.py` runs the four cases, attaches `OpikTracer`, logs the `answer_has_fact` score, and flushes.
- `rag.py` loads and chunks the handbook, builds the retriever and the chain, and holds the traced `search_handbook` tool.
- `checks.py` holds the four test cases (question, expected fact, expected source file) and the scoring function.
- `data/` is the four-file fictional handbook.
- `docker-compose.yml` starts an Ollama server if you need one.
- `tests/test_rag.py` covers chunking, that every case's fact exists in its source file, context formatting, the score, the chain with a stub retriever and a fake LLM, and the traced tool with tracking disabled.
- `tests/conftest.py` sets `OPIK_TRACK_DISABLE=true` so tests never need a server.

*built with Opik · inspired by Opik's examples and documentation*
