<div align="center">

# 🎲 Board-Game Café Rules Helper

**`langchainjs-board-game-rules-chat`**

*A rules-question chat widget whose Opik threads read like a transcript, not like JSON.*

![Node](https://img.shields.io/badge/node-20%2B-339933?style=flat&logo=nodedotjs&logoColor=white)
![LangChain.js](https://img.shields.io/badge/langchain.js-1.x-1C3C3C?style=flat)
[![Opik](https://img.shields.io/badge/opik--langchain-2.3.2-2f54eb?style=flat)](https://github.com/comet-ml/opik)

</div>

---

Picture a tablet on every table at the Moss & Meeple café. A guest types "can I grab two lanterns in one turn?", the helper answers from the house rulebook, and ten minutes later the same table asks a follow-up. Behind that tablet is a stateless `POST /chat`, so by default your tracing sees a pile of unrelated requests. When a host says "the helper told table 9 the wrong thing", you want that table's whole conversation, in order, readable at a glance. This example wires that up with LangChain.js, Express and the `opik-langchain` callback, and shows what happens to the transcript view when the chain's root takes an object instead of a string.

## What you'll build

- An Express server with `POST /chat { message, sessionId }` and a small tablet-style page at `/`.
- A LangChain.js chain: load the table's history and retrieve rule passages, fill a prompt, call `gpt-4o-mini`, parse to a string. The root takes a question string and returns an answer string.
- An offline corpus of four invented games in `data/rules/` (Lantern Heist, Moth & Marmalade, Tidewalkers, Quill & Cauldron), split per section and searched by keyword overlap. No embeddings, no vector store.
- One `OpikCallbackHandler` per table with `threadId` set to the `sessionId`.
- `npm run demo`: three tables play scripted conversations. Two use the plain string root. The third (`table-12-object-root`) asks Lantern Heist questions through a variant whose root takes `{ question }` and returns `{ answer }`, so you can compare the two shapes side by side.

## See it in Opik

Open the **`langchainjs-board-game-rules-chat`** project. After one demo run it holds **8 traces** (6 + 2 turns), **46 spans**, and **3 threads**.

- **Traces tab:** every row is named `rules-helper-turn`. Open one string-root turn: 5 spans. `rules-helper-turn` contains `load-table-context` (the history plus retrieval step), `ChatPromptTemplate`, `ChatOpenAI` (type `llm`, model `gpt-4o-mini`, about 340 prompt and 17 completion tokens, cost around $0.00006), and `StrOutputParser`. Open the `ChatPromptTemplate`/`ChatOpenAI` input to read the exact rule excerpts the model was given. When an answer is wrong, you can tell whether retrieval or the model was at fault.
- **Threads tab:** `table-4-lantern-heist` and `table-9-tidewalkers` have 6 messages each (3 questions, 3 answers) in turn order. Their first and last messages are the guest's sentence and the helper's sentence. `table-12-object-root` has 4 messages, but they are the structured objects `{"question": ...}` and `{"answer": ...}`, which is what that thread's messages contain instead of plain sentences. Same app, same model, same questions; only the root's type differs.
- Open an object-root trace: it has 8 spans, the extra three being the wrapper sequence plus `unwrap-question` and `wrap-answer`.

The whole demo run cost under a tenth of a cent in model usage.

## Run it yourself

1. `cp .env.example .env` and add `OPENAI_API_KEY` (or rely on a repo-root `.env`). For a local Opik, the defaults in `.env.example` work; for Opik Cloud set `OPIK_API_KEY` and unset `OPIK_URL_OVERRIDE`.
2. `npm install`
3. `npm run demo` (about 40 seconds; it plays the three tables and flushes traces).
4. Open the project in Opik (local default UI: `http://localhost:5173`) and check Traces and Threads.
5. For the widget itself: `npm run dev`, then visit `http://localhost:4170`. Each browser tab is a table with its own thread.
6. Offline tests: `OPIK_TRACK_DISABLE=true npm test` (needs no keys).

## Poke around

- Open the widget in two tabs and ask the same question. Two `sessionId`s, two threads, and the second tab's helper knows nothing about the first.
- Ask "can we play it with a dragon expansion?" and open the trace: retrieval finds passages, but the prompt tells the model to defer to the host. Edit `SYSTEM_PROMPT` in `src/chat.ts` and watch it improvise instead.
- Ask a vague follow-up like "and can I trade it?" with no game named. Retrieval also searches the previous question; delete that line in `loadContext` and compare the excerpts in the `ChatPromptTemplate` span.
- Send `"rootShape": "object"` in a curl request to `/chat` for any `sessionId` and see that thread turn into JSON.

## Gotchas we hit

**`npm install` fails with `ERESOLVE ... peer opik@"^1.8.75" from opik-langchain@2.3.2`.** `opik-langchain` declares a stale peer range, so it rejects the current `opik` 2.3.2. Add an override so npm reuses your top-level `opik`:

```json
"overrides": { "opik-langchain": { "opik": "$opik" } }
```

**The thread transcript shows `{"question": ...}` / `{"answer": ...}` instead of sentences.** Opik shows the root run's input and output. If the root chain takes and returns objects, the thread messages are those objects. Keep the root `string -> string` and do the object plumbing (history, retrieval) inside the first step, as `buildChain` does in `src/chat.ts`. Pass the session through `configurable: { sessionId }` rather than the input.

**Traces missing at the end of a script.** The client buffers; `await opikClient.flush()` (see `flushOpik` in `src/server.ts`) before exiting, and on `SIGINT` in `npm run dev`.

## How it's put together

- `src/rules.ts`: parses the markdown corpus into passages, tokenizes, keyword-scores and formats them.
- `src/chat.ts`: the system prompt, the string-in/string-out chain, the object-root variant, history helpers.
- `src/server.ts`: Express app, per-table sessions and Opik handlers, shared Opik client and flush.
- `src/demo.ts`: starts the server, plays three tables, flushes, exits.
- `public/index.html`: the tablet widget; one `sessionId` per tab.
- `data/rules/*.md`: four fictional rulebooks.
- `tests/rules.test.ts`: corpus parsing, tokenizing, retrieval.
- `tests/chain.test.ts`: the chain with a fake model, session errors, and a run with the Opik handler attached while tracking is off (`OPIK_TRACK_DISABLE=true`, set in `vitest.config.ts`).

---

*built with Opik · inspired by Opik's examples and documentation*
