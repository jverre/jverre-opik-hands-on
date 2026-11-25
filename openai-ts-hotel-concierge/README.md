# openai-ts-hotel-concierge

*A chat concierge for hotel guests, traced so every message, tool call and cent is visible in Opik.*

![TypeScript](https://img.shields.io/badge/TypeScript-strict-3178C6?style=flat&logo=typescript&logoColor=white)
![OpenAI SDK](https://img.shields.io/badge/openai-6.x-412991?style=flat&logo=openai&logoColor=white)
[![Opik](https://img.shields.io/badge/Opik-2.3.2-2f54eb?style=flat)](https://github.com/comet-ml/opik)

A guest in room 412 asks about a late checkout, then a massage, then dinner. The model is called two or three times per message (once more whenever it uses a tool), and every call re-sends the whole conversation so far. Plain request logs show you a pile of unrelated completions. They cannot tell you which guest conversation a call belonged to, what that conversation cost, or whether the guest was happy at the end.

This project is a small concierge for the fictional Harbourlight Hotel, built on the OpenAI TypeScript SDK with no agent framework. It handles late checkout questions, spa availability, restaurant tips and housekeeping requests. It deliberately does **not** book trips, flights or rooms, and says so when asked. Opik turns its traffic back into conversations.

## What you'll build

- `Concierge` keeps one message history per guest and runs a short tool loop: `check_spa_slots` reads availability, `log_housekeeping_request` creates a ticket.
- Each guest message becomes one Opik trace named `concierge-turn`. Its `threadId` is the conversation id, so turns of one chat group together.
- The OpenAI client is wrapped with `opik-openai` (`trackOpenAI`), so each model call is recorded with the model, token usage and estimated cost. Tool executions are logged as `tool` spans.
- After the run, simulated guest ratings are written as a `guest-satisfaction` feedback score on two specific traces, and the script reads the project back to print tokens and cost per message.

## See it in Opik

Open Opik (`http://localhost:5173` for a local install) and pick the project **openai-ts-hotel-concierge**.

**Traces tab.** After one demo run there are 6 traces, all named `concierge-turn`. The Input column shows the guest's message and Output shows the concierge's reply. The Cost column is per message: from `$0.000099` for the first late-checkout question (528 tokens) up to `$0.000213` for the spa question (1,240 tokens), which needed a tool call and therefore two model calls. The whole run costs about `$0.0008`. Tokens climb within a conversation because history is re-sent each time.

**Open the spa trace** (`room-412-late-checkout-and-spa`, turn 2). It holds two model spans plus a `check_spa_slots` span. The tool span shows the arguments the model chose (`{"day":"today"}`) and the two open slots returned (15:30 and 17:00; the 14:00 slot is taken and filtered out). The model spans show `gpt-4o-mini-2024-07-18` with prompt and completion tokens and their cost. The same pattern appears on the towels trace in the other conversation, with a `log_housekeeping_request` span and ticket `HK-101`.

**Threads tab.** Two threads, `room-412-late-checkout-and-spa` and `room-208-towels-and-trip-ask`, each with 6 messages (3 guest, 3 concierge) readable as a transcript.

**Feedback column.** Two traces carry `guest-satisfaction`: the dinner recommendation scores `1`, and the flight-booking refusal in room 208 scores `0` ("Guest wanted the flight booked, not a redirect."). Sort or filter on that column to find unhappy conversations first. The refusal is correct behaviour for this bot, which is the point: a low score is not always a bug, but now you can see it and decide.

In the terminal, the run ends with a table read back from Opik, so you can compare numbers without opening the UI:

```
room-412-late-checkout-and-spa     turn 2   1240 tokens  $0.000213
room-412-late-checkout-and-spa     turn 3    745 tokens  $0.000140  guest-satisfaction=1
room-208-towels-and-trip-ask       turn 2    604 tokens  $0.000102  guest-satisfaction=0
```

One thing to know: in opik-openai 2.3.2 the model call spans are typed `general`, not `llm`. Model, usage and cost are still recorded and shown.

## Run it yourself

1. Start a local Opik (see the Opik self-hosting docs) or use Opik Cloud.
2. `cp .env.example .env` and set `OPENAI_API_KEY`. The app also finds a `.env` in any parent folder. For Opik Cloud, set `OPIK_URL_OVERRIDE`, `OPIK_WORKSPACE` and `OPIK_API_KEY`; the defaults target a local Opik at `http://localhost:5173/api/`.
3. `npm install`
4. `npm run demo` (about a minute, under a cent with `gpt-4o-mini`)
5. Open the `openai-ts-hotel-concierge` project in Opik and look at Traces, then Threads.
6. `npm test` runs the offline tests (no keys, nothing sent to Opik).

## Poke around

- `npm run dev` starts an interactive chat. It appears as a new thread (`interactive-...`) while you type. Press Ctrl+D to quit.
- Ask for something the concierge must refuse ("book me a table on the Eurostar") and open the trace. Does it redirect to the front desk or improvise?
- Change `MODEL` in `src/hotel.ts` to `gpt-4.1-mini` and compare the Cost column for the same six messages.
- Ask for "three pillows and a turndown for room 412 and also a spa slot tomorrow". Count the tool spans and model spans in one trace.

## Gotchas we hit

**`npm install` fails with `ERESOLVE ... peer opik@"^1.8.61" from opik-openai@2.3.2`.** `opik-openai` 2.3.2 still declares a peer dependency on `opik` 1.x, while the current SDK is 2.x. Tell npm the pair is fine with an `overrides` block in `package.json`:

```json
"overrides": { "opik-openai": { "opik": "$opik" } }
```

**TypeScript says `Property 'id' does not exist on type 'Trace'`.** The trace id lives under `data`: use `trace.data.id` (this project exposes it as `TurnTrace.traceId`).

## How it's put together

- `src/hotel.ts` — model name, the concierge system prompt, and the fictional spa and housekeeping data.
- `src/tools.ts` — tool schemas and the functions behind them.
- `src/concierge.ts` — per-guest history and the tool loop around the OpenAI client.
- `src/tracing.ts` — the Opik client, one trace per turn, `trackOpenAI` wrapping, tool spans, flush.
- `src/report.ts` — reads traces back from Opik and prints tokens, cost and scores per message.
- `src/demo.ts` — two scripted conversations, feedback logging, and the interactive mode.
- `src/env.ts` — loads the nearest `.env`.
- `tests/` — vitest, offline: tool behaviour, the tool loop through a stub model with tracking disabled (`OPIK_TRACK_DISABLE=true`, set in `vitest.config.ts`), and the report formatting.

---

*built with Opik · inspired by Opik's examples and documentation*
