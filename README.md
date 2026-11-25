# jverre-opik-hands-on 🧗

**23 small, runnable apps, each one showing a single thing you can do with [Opik](https://github.com/comet-ml/opik):
trace an agent, group a chat into threads, version a prompt, gate a change with a test suite, attach audio
to a trace, or ingest OpenTelemetry from a JVM service.**

![examples](https://img.shields.io/badge/examples-23-informational) ![Python](https://img.shields.io/badge/Python-13-3776AB) ![TypeScript](https://img.shields.io/badge/TypeScript-7-3178C6) ![Java](https://img.shields.io/badge/Java-1-ED8B00) ![low--code](https://img.shields.io/badge/low--code-2-8E44AD) ![license](https://img.shields.io/badge/license-Apache%202.0-blue)

Every app here is small enough to read in one sitting, runs on fictional data that ships in its folder, and logs to
its own Opik project named after its folder. Each README says what to open in Opik and what you should see there,
with the numbers from a real run, including the runs where the model got something wrong. Those are often the most
useful part.

## Pick one

### Tracing agents and frameworks

| Example | Stack | What it shows |
|---|---|---|
| [openai-agents-insurance-claims](openai-agents-insurance-claims) | Python · OpenAI Agents SDK | A triage agent hands home-insurance claims to specialists; handoff and tool-call spans, one thread per claim |
| [crewai-street-festival-planner](crewai-street-festival-planner) | Python · CrewAI | Three agents plan a street festival; one trace per kickoff with tokens and dollars per agent |
| [langgraph-incident-postmortem](langgraph-incident-postmortem) | Python · LangGraph | Planner → investigator loop → writer drafts a post-mortem; one deep trace, cost per agent |
| [mastra-library-holds-agent](mastra-library-holds-agent) | TypeScript · Mastra (OTel) | A library desk agent with holds, renewals and fines tools; agent loops with real `execute_tool` spans |
| [beeai-py-expense-approval](beeai-py-expense-approval) | Python · BeeAI (OpenInference) | A ReAct agent triages expense reports; LLM and tool spans from OpenInference, cost recovered by mapping the provider |
| [pydantic-ai-wine-tasting-notes](pydantic-ai-wine-tasting-notes) | Python · Pydantic AI (OTel) | Typed extraction of tasting notes over the Logfire/OTel bridge, plus a suite that catches invented values |
| [temporal-py-grant-review](temporal-py-grant-review) | Python · Temporal | A durable grant-review workflow; one trace across client and worker processes, with the retried activity's error |
| [opik-py-redaction-pipeline](opik-py-redaction-pipeline) | Python · Opik SDK only | A PII-redaction pipeline traced by hand: manual spans, hand-recorded usage, a guardrail span, feedback scores |

### Chat apps and threads

| Example | Stack | What it shows |
|---|---|---|
| [openai-ts-hotel-concierge](openai-ts-hotel-concierge) | TypeScript · OpenAI SDK + `opik-openai` | A hotel guest-services chat; threads per room, cost per turn, a guest-satisfaction score |
| [langchainjs-board-game-rules-chat](langchainjs-board-game-rules-chat) | TypeScript · LangChain.js + Express | A board-game café rules helper; why a string-in/string-out root makes threads read like a transcript |
| [vercel-ai-bike-repair-chat](vercel-ai-bike-repair-chat) | TypeScript · Vercel AI SDK + Next.js | A streaming bike-repair assistant; streaming spans, threads, and a live online-evaluation rule scoring each turn |
| [dify-climbing-gym-assistant](dify-climbing-gym-assistant) | Dify (Docker) | A climbing-gym front desk built in Dify; Dify's built-in Opik tracing, one thread per conversation |

### Evaluation, test suites and prompts

| Example | Stack | What it shows |
|---|---|---|
| [langgraph-museum-guide-rag](langgraph-museum-guide-rag) | Python · LangChain + LangGraph | Two-node RAG over a museum guide; a dataset and two experiments scored for hallucination and context precision |
| [llamaindex-trail-guide-qa](llamaindex-trail-guide-qa) | Python · LlamaIndex | Q&A over generated trail-guide PDFs; retrieval and synthesis spans, a section-level test suite |
| [openai-vision-shipping-labels](openai-vision-shipping-labels) | Python · OpenAI vision | Field extraction from generated shipping labels; images on the trace, a suite with honest failures |
| [opik-ts-podcast-title-prompts](opik-ts-podcast-title-prompts) | TypeScript · Opik SDK | A podcast title prompt in the prompt library; v1 fails the suite, v2 passes it |
| [dspy-astronomy-fact-check](dspy-astronomy-fact-check) | Python · DSPy | A claim checker scored on one suite before and after compiling: 0/8 → 8/8 |
| [optimizer-recipe-cuisine-classifier](optimizer-recipe-cuisine-classifier) | Python · Opik Agent Optimizer | A cuisine classifier prompt optimized against a dataset; the score curve and the winner saved as a prompt version |

### Media and multimodal

| Example | Stack | What it shows |
|---|---|---|
| [openai-ts-storybook-illustrations](openai-ts-storybook-illustrations) | TypeScript · OpenAI images | Picture-book pages from prompt-library briefs; generated PNGs attached to each trace, brief v1 vs v2 |
| [openai-ts-vet-voicemail-triage](openai-ts-vet-voicemail-triage) | TypeScript · OpenAI TTS + transcription | Vet-clinic voicemails → transcript → urgency; a playable MP3 on every trace, judge noise tamed with repeated runs |

### Local models, JVM and low-code

| Example | Stack | What it shows |
|---|---|---|
| [ollama-homebrew-rag](ollama-homebrew-rag) | Python · Ollama + LangChain | Fully local RAG over a homebrewing handbook; zero cloud calls, and a retrieval span that LangChain alone drops |
| [quarkus-langchain4j-pharmacy-faq](quarkus-langchain4j-pharmacy-faq) | Java · Quarkus + LangChain4j (OTLP) | A pharmacy FAQ bot exporting OpenTelemetry; prompt and completion on the spans, cost computed by Opik |
| [n8n-hackathon-screening](n8n-hackathon-screening) | n8n (Docker) | A no-code screening workflow traced with `n8n-observability`: one trace per execution, one span per node |

## Run one

1. **Start Opik.** A local Opik is the easiest: follow the
   [self-hosting guide](https://www.comet.com/docs/opik/self-host/local_deployment); the UI ends up on
   `http://localhost:5173`. Opik Cloud works too: set `OPIK_URL_OVERRIDE`, `OPIK_WORKSPACE` and `OPIK_API_KEY`.
2. **Fill in the shared `.env` once.** Copy `.env.example` to `.env` at the repo root and add your
   `OPENAI_API_KEY`. Every example walks up to the repo root to find it.
3. **Go into a folder and follow its README.** In general:
   - Python: `uv sync && uv run main.py` (needs [uv](https://docs.astral.sh/uv/))
   - TypeScript: `npm install && npm run demo` (Node 20+)
   - Java: `./run.sh` (JDK 21+, Maven)
   - n8n and Dify: `./setup.sh && ./demo.sh` (Docker)
4. **Open Opik** and pick the project with the same name as the folder.

One run of any example costs from nothing (Ollama) to a few cents (the ones with LLM-judge test suites).

## What's in a folder

- A `README.md` that explains the problem, shows what to look at in Opik, lists exact commands, and ends with a
  **Gotchas** section: real problems hit while building it, each with the symptom, the cause and the fix.
- The app itself, with a short comment at every place it touches Opik saying why that call is there and what it
  produces.
- `data/` or `docs/` with the fictional data the app reads.
- Offline tests for every Python and TypeScript example (`uv run pytest` or `npm test`). They need no API key and
  run with Opik tracking off.
- A `.env.example` that lists only the variables that example reads.

The git history is part of the material: most examples arrive as a few commits, typically the plain app first, then
the change that adds Opik, then the evaluation layer. `git log -p -- <folder>` shows exactly what adding Opik to an
existing app looks like.

## License

[Apache 2.0](LICENSE).

---

*Inspired by Opik's examples and documentation · [Opik on GitHub](https://github.com/comet-ml/opik) ·
[Opik docs](https://www.comet.com/docs/opik/)*
