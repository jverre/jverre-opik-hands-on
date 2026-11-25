# quarkus-langchain4j-pharmacy-faq

![Java](https://img.shields.io/badge/java-21%2B-ED8B00?style=flat&logo=openjdk&logoColor=white)
![Quarkus](https://img.shields.io/badge/quarkus-3.40-4695EB?style=flat&logo=quarkus&logoColor=white)
![LangChain4j](https://img.shields.io/badge/quarkus--langchain4j-1.13-1C3C3C?style=flat)
[![Opik](https://img.shields.io/badge/Opik-OpenTelemetry-2f54eb?style=flat)](https://github.com/comet-ml/opik)

**A pharmacy medication FAQ bot on Quarkus, with every answer and every retrieved passage traced into Opik over plain OTLP.**

A customer asks a pharmacy chatbot whether they can take one pill with another. The answer is
short, polite, and ends with "confirm with a pharmacist". Was it right because the formulary said
so, or because the model improvised? Nobody can tell from the response alone, and in a health
setting "it sounded fine" is not good enough. This example is a small Quarkus service for a
made-up chain, Harbourlight Pharmacy, where each reply leaves behind a trace showing the passages
that were retrieved, the exact prompt the model saw, the completion, the token counts, and the
dollar cost. There is no Opik SDK on the JVM side: Quarkus emits OpenTelemetry spans and Opik
ingests them.

## What you'll build

A Quarkus REST service with one endpoint, `GET /ask?q=...`, on port 4300.

- **Corpus.** Six fictional medicines (Calmorex, Lumidine, Ferravel, Solvane, Tendrix, Clotavar)
  in `src/main/resources/formulary/`, each with Dosage forms, Storage, and Common interactions
  sections. At startup every section becomes a chunk, embedded with `text-embedding-3-small` into
  an in-memory LangChain4j store (18 chunks).
- **Retrieval.** `FormularyIndex` embeds the question and takes the three closest chunks.
- **Generation.** `PharmacyAssistant` is a `@RegisterAiService` interface on `gpt-4o-mini`. Its
  system prompt says: answer only from the excerpts, never give a personal dose, never declare a
  combination safe for a specific person, and always end by deferring to a pharmacist.
- **Tracing.** `quarkus-opentelemetry` plus five lines of `application.properties`. No Opik
  dependency anywhere in the `pom.xml`.
- **Demo script.** `run.sh` builds the jar, starts the service, asks five scripted questions
  (a storage question, a two-drug interaction, a blood-thinner question, a request for a child's
  dose, and a medicine the formulary does not stock), and shuts the service down.

## See it in Opik

Open the project **`quarkus-langchain4j-pharmacy-faq`** (self-hosted default: http://localhost:5173).
After one run it holds **6 traces**: five named `GET /ask`, one per question, and one named
`index_formulary` from startup, whose single embeddings call produced "indexed 18 embeddings".

Open the trace for *"I take Clotavar. Is Tendrix okay for my back pain?"* (about 1.8 s). Its tree has
six spans:

1. `GET /ask`, the Quarkus server span. Its Input and Output are the question and the final answer,
   so the trace table's columns are readable without clicking in.
2. `retrieve_formulary`, our own span. Output lists the three chunks with similarity scores:
   `Tendrix / Common interactions` (0.839), `Tendrix / Dosage forms` (0.786) and
   `Clotavar / Common interactions` (0.779). The answer is a good one because the first chunk
   literally says to speak to a pharmacist before combining the two.
3. `langchain4j.aiservices.PharmacyAssistant.answer`, the AI-service call Quarkus creates for you.
4. `completion gpt-4o-mini`, the only span of type `llm`. Open it to see model `gpt-4o-mini`,
   provider `openai`, 327 prompt + 50 completion = 377 tokens, an estimated cost of about
   $0.00008, the full prompt (system rules, the three excerpts, the question) and the completion.
   Across the five questions the whole run used about 1,800 tokens, around $0.0004.
5. `POST /embeddings` and `POST /chat/completions` are the HTTP-client spans Quarkus adds for the
   raw OpenAI requests; they carry only URL and status and are type `general`.

Two comparisons are worth making. The Zentavo question (a drug that is not in the formulary)
retrieves the three Tendrix chunks at scores around 0.70, noticeably lower than the 0.84 to 0.85 of the
good matches, and the model correctly answers "the formulary has no information". The child-dose
question retrieves the right Calmorex chunks (0.83) but the answer still declines to give a dose.
Both refusals are visible as policy at work, not luck, because you can see the context the model
was given.

**Cost.** This one works without any extra mapping: the spans carry `gen_ai.*` attributes and a
provider that Opik recognises, so `gpt-4o-mini` calls arrive with usage and a computed
`total_estimated_cost` (for the question above, 327 x $0.15/M + 50 x $0.60/M = $0.0000790).
If you switch `quarkus.langchain4j.openai` to a custom base URL or a model Opik does not price,
expect usage without a dollar figure.

## Run it yourself

1. Install JDK 21 or newer and Maven 3.9+. Start a local Opik
   ([self-hosting guide](https://www.comet.com/docs/opik/self-host/local_deployment)).
2. `cp .env.example .env` and set `OPENAI_API_KEY` (or reuse a repo-root `.env`; `run.sh` loads
   `../.env` and `./.env`). Defaults point at `http://localhost:5173/api/` and workspace `default`.
3. `./run.sh`. It builds, starts the service on :4300, asks the five questions, and stops the
   service (SIGTERM, so the exporter flushes). Takes under a minute including the build.
4. Open the `quarkus-langchain4j-pharmacy-faq` project in Opik and click the newest `GET /ask` trace.
5. For your own questions: `./run.sh serve`, then
   `curl --get --data-urlencode "q=Where should I keep Ferravel?" http://localhost:4300/ask`

Using Opik Cloud instead: set `OPIK_OTEL_ENDPOINT=https://www.comet.com/opik/api/v1/private/otel`
and add `Authorization=<your key>,` at the start of the `quarkus.otel.exporter.otlp.traces.headers`
value in `application.properties`.

## Poke around

- Set `quarkus.langchain4j.tracing.include-prompt=false` and `include-completion=false`, then rerun.
  The `completion gpt-4o-mini` span keeps its model, tokens and cost but its Input and Output lose
  the prompt and completion text.
- Change `TOP_K` in `FormularyIndex` from 3 to 1 and ask the Lumidine and Ferravel question. The
  retrieval span's output shrinks to a single chunk; read it and judge whether the answer still has
  what it needs.
- Weaken the system prompt in `PharmacyAssistant` (drop the "never recommend a personal dose" line)
  and ask for the child's dose. Compare the new completion span against the old one.
- Add a seventh file under `formulary/` and list it in `Formulary.FILES`; the new chunks appear in
  the retrieval output on the next run.

## Gotchas we hit

**The `completion gpt-4o-mini` span has a model and token counts but no prompt or completion text.**
Quarkus LangChain4j leaves message content off spans unless you ask for it. Turn it on:
```properties
quarkus.langchain4j.tracing.include-prompt=true
quarkus.langchain4j.tracing.include-completion=true
```
Think before enabling this with real customer data; medication questions are personal.

**There is no span for the vector search.** The trace shows the AI-service call and the OpenAI
request but nothing about which chunks were fetched, because the in-memory store is called directly.
Wrap the lookup in a span and set `input` / `output` attributes (Opik maps those names onto the
span's Input and Output panels); see `FormularyIndex.retrieve`:
```java
Span span = tracer.spanBuilder("retrieve_formulary").startSpan();
span.setAttribute("input", json(input));
span.setAttribute("output", json(output));
```

**An unexpected `GET /` trace with no LLM call appears next to your questions.** A readiness probe
that curls the server before the demo also becomes a trace. `run.sh` waits for the "Listening on"
log line instead, so the project holds only real work.

**The first trace of every run is a bare `POST /embeddings`.** Startup indexing runs outside any
request, so its embeddings call becomes an anonymous root trace. Opening a named span around it
(`index_formulary`) makes it recognisable.

## How it's put together

- `pom.xml` — Quarkus 3.40 and the LangChain4j platform BOMs; `quarkus-langchain4j-openai` and `quarkus-opentelemetry`. No Opik dependency.
- `src/main/resources/application.properties` — model choices, the OTLP endpoint and Opik headers (workspace and project), and the two flags that put prompt and completion on spans.
- `src/main/resources/formulary/*.md` — the six fictional medicine entries that form the corpus.
- `src/main/java/com/example/pharmacy/Formulary.java` — loads the files and splits them into one chunk per section.
- `src/main/java/com/example/pharmacy/FormularyIndex.java` — embeds and stores chunks at startup (`index_formulary` span) and answers queries (`retrieve_formulary` span).
- `src/main/java/com/example/pharmacy/PharmacyAssistant.java` — the AI service with the pharmacist-deferring system prompt.
- `src/main/java/com/example/pharmacy/AskResource.java` — the `/ask` endpoint; copies question and answer onto the root span.
- `run.sh` — build, start, ask five questions, stop. Derives the OTLP endpoint from `OPIK_URL_OVERRIDE`.

The medicines, doses, and rules here are invented for the demo. This is not medical advice.

---

*built with Opik · inspired by Opik's examples and documentation*
