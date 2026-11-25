# vercel-ai-bike-repair-chat

*Spoke, a streaming bike-repair assistant for a community workshop, with every reply traced, threaded and judged in Opik.*

![TypeScript](https://img.shields.io/badge/typescript-5.6%2B-3178C6?style=flat&logo=typescript&logoColor=white)
![Next.js](https://img.shields.io/badge/next.js-16-000000?style=flat&logo=nextdotjs&logoColor=white)
![Vercel AI SDK](https://img.shields.io/badge/ai%20sdk-7-000000?style=flat&logo=vercel&logoColor=white)
![opik-vercel](https://img.shields.io/badge/opik--vercel-2.2.89-2f54eb?style=flat)

A rider asks why their chain squeaks, the assistant streams an answer a word at a time, and then
the request is over. Nothing in your code ever holds "the answer" as a return value, every request
re-sends the whole conversation, and a flaky answer on turn three only makes sense next to turns
one and two. This example is a small chat for the Cobblestone Cycle Co-op, a made-up volunteer
bike workshop, built to show how to get all of that into Opik without wrapping a single model call.

## What you'll build

- **A Next.js chat route** (`app/api/chat/route.ts`) that stays thin and hands the request to
  `lib/chat.ts`, which calls `streamText` on `gpt-4o-mini` and streams the reply back.
- **A price-lookup tool** (`lib/tools.ts`) over a fictional service list (`lib/workshop.ts`), so
  some turns are two model steps with a tool call in the middle.
- **One exporter, two settings.** `instrumentation.node.ts` registers `OpikExporter` from
  `opik-vercel` plus the AI SDK's OpenTelemetry integration. `lib/telemetry.ts` holds the
  per-call settings and the thread-id mapping.
- **A scripted rider** (`scripts/demo.ts`) that creates an online evaluation rule, boots the app
  on a private port, plays three conversations, waits for the judge scores, and shuts down.
- **A live LLM-as-judge rule** (`lib/online-rule.ts`) named `actionable_workshop_advice` that
  scores every new trace true or false for "did this reply give the rider something concrete".

```
scripted rider -> POST /api/chat -> streamText(gpt-4o-mini, getServicePrice) -> tokens stream back
                                   \-> AI SDK spans -> OpikExporter -> Opik trace + spans
                                                                        \-> online rule -> judge score
```

## See it in Opik

Open the `vercel-ai-bike-repair-chat` project and start on **Traces**. After one demo run it holds
five `workshop-chat-turn` traces, one per question the scripted rider asked, plus seven
`online_evaluation` traces that are the judge's own model calls (the rule's work is traced too).

Open the second turn of the chain conversation ("Lube didn't fix it. How much would the
workshop charge to replace the chain?"). Its span tree has two `llm` spans named
`chat gpt-4o-mini`, with a `tool` span `execute_tool getServicePrice` between them, all under
`general` spans `step 1` and `step 2`. The tool span shows the arguments the model chose and the
text it got back (`Chain replacement: suggested labour donation GBP 6, about 25 minutes`).
That turn used 725 prompt tokens and 63 completion tokens, and Opik priced it at $0.00014655.
The first turn of the same chat used 264 prompt tokens: the history is re-sent every turn, so the
prompt grows as the conversation does.

Switch to the **Threads** tab. The three chats show up as three threads, each stitched from its
turns: the chain squeak (2 turns), the spongy rear brake (2 turns), and a deliberately off-topic
question about bleeding the brakes on a Honda Civic (1 turn). The chat id from the request body
travels through `runtimeContext` into a span attribute, which is what makes the grouping work.

Back on Traces, look at the **Feedback scores** column. The rule scored four of the five chat turns
`actionable_advice = 1` and the car question `0`: Spoke correctly declined ("I only assist with
bicycles, so I'm unable to help with your Honda Civic"), and the judge, which asks for something concrete to act on, marks that as
not helpful. That is the point of the rule: it is judging usefulness, not politeness, and
it ran on the server as the traces arrived. The project's online evaluation rules list
`actionable_workshop_advice` with a 100% sampling rate.

## Run it yourself

1. Copy `.env.example` to `.env` and fill in `OPENAI_API_KEY` (or keep keys in a `.env` one folder up;
   both are read). For a local Opik the defaults already point at `http://localhost:5173/api/`.
2. `npm install --no-audit --no-fund`
3. `npm run demo`. It creates the rule if it is missing, starts the server on port 4191, plays the
   three conversations (about 30 seconds and a fraction of a cent of model spend), prints the judge scores
   and stops the server.
4. `npm run verify` prints what the project holds: traces, span types, tokens, cost, scores.
5. Open `http://localhost:5173` (or your Opik Cloud workspace), project `vercel-ai-bike-repair-chat`.
6. Want to chat yourself? `npm run dev` and open `http://localhost:3000`. Each browser tab is its own thread.
7. `npm test` runs the offline tests. They need no keys and send nothing to Opik. Set
   `OPIK_TRACK_DISABLE=true` to switch the telemetry spans off, as the tests do (an app-level
   switch in `lib/telemetry.ts`; the TypeScript SDK has no global off switch of its own).

## Poke around

- Ask Spoke "how much for a tune-up?" in `npm run dev`. The price tool is matched by keyword in
  `lib/workshop.ts`; see what the tool span returns when nothing matches.
- Change `samplingRate` in `lib/online-rule.ts` to `0.5`. The rule is created once, so delete
  `actionable_workshop_advice` in the project's rules first, then re-run and count which traces get scored.
- Swap `gpt-4o-mini` for `gpt-4.1-mini` in `lib/chat.ts` and compare the cost column per turn.
- Loosen the "bicycles only" line in `lib/prompt.ts` and re-run: does the Civic question flip to `1`?

## Gotchas we hit

**`npm install` fails with `ERESOLVE ... peer @opentelemetry/api@">=1.10.0 <1.11.0" from @opentelemetry/sdk-node@0.301.2`.**
`opik-vercel` has loose peer ranges on `@opentelemetry/sdk-node`, and npm picks the newest one,
which wants a newer `@opentelemetry/api` than `opik-vercel`'s other peers allow. Pin the three
OpenTelemetry packages in `package.json` (as this example does):
`"@opentelemetry/api": "1.9.1"`, `"@opentelemetry/core": "2.11.0"`, `"@opentelemetry/sdk-node": "0.222.0"`.

**The demo hangs, then `TypeError: fetch failed` with the cause `Error: bad port`.**
The server is up (`curl` works) but Node's `fetch` refuses to talk to a handful of "unsafe"
ports, and 4190 is one of them. Pick a different port: the demo uses 4191 and reads `DEMO_PORT`.

**The judge shows up as extra traces in the project.**
The online rule's own model calls are logged in the same project as `online_evaluation` traces.
Filter on the trace name `workshop-chat-turn` when you count chat turns (the demo and `verify`
scripts do).

## How it's put together

- `app/api/chat/route.ts`: thin route handler, parses the body and streams the reply back.
- `app/page.tsx`, `app/layout.tsx`: the `useChat` UI.
- `lib/chat.ts`: `streamRepairReply` (the `streamText` call, model injectable) and request parsing.
- `lib/telemetry.ts`: project and trace names, per-call telemetry settings, thread-id mapping.
- `lib/online-rule.ts`: creates the project and the `actionable_workshop_advice` judge rule once.
- `lib/prompt.ts`, `lib/tools.ts`, `lib/workshop.ts`: the system prompt, the price tool, the fictional price list.
- `instrumentation.ts`, `instrumentation.node.ts`: Next.js entry point and the Opik exporter setup.
- `scripts/demo.ts`, `scripts/conversations.ts`, `scripts/sse.ts`: the scripted rider and its stream reader.
- `scripts/verify.ts`: reads the project back from Opik and prints what it holds.
- `tests/`: vitest suites for the price lookup and tool, telemetry helpers, request parsing, the streaming
  call with tracking switched off, and the SSE reader. They run offline in about two seconds.

---

*built with Opik · inspired by Opik's examples and documentation*
