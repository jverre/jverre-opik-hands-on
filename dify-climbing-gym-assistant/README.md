# dify-climbing-gym-assistant

**A Dify chat app for a climbing gym's front desk, traced into Opik with Dify's built-in Opik provider: no code in the app, one setting per app.**

![Dify](https://img.shields.io/badge/Dify-1.17.1-1C64F2) ![model](https://img.shields.io/badge/model-gpt--4o--mini-412991) ![runs in](https://img.shields.io/badge/runs%20in-Docker-2496ED)

Basalt Wall is a fictional indoor climbing gym. Its front-desk assistant, built in Dify, answers the questions the
staff get all day: which membership is cheapest, how to freeze one, what you need before you can top-rope or lead,
and when the boulder problems are reset. All the gym facts live in the app's instructions.

A chatbot like this is easy to ship and hard to audit. When a member says "the bot told me the freeze was free",
someone needs to see exactly what the model was given and what it answered. Dify can send every message to Opik
itself: you save an Opik config on the app and turn tracing on, and each answer becomes a trace with the full
prompt, the reply and the token counts, grouped by conversation.

## What you'll build

- Dify 1.17.1 in Docker (the upstream compose files are vendored in `dify-docker/`).
- A chat app, **Basalt Wall Front Desk**, imported from `app/basalt-wall-front-desk.yml` and running on
  gpt-4o-mini.
- `configure_dify.py`, which does everything the Dify UI would: the admin account, the OpenAI plugin and key, the app
  import, the Opik tracing config, and a service API key.
- `demo.sh`, which asks four questions in one conversation through Dify's service API.
- `check_opik.py`, which reads the traces back from Opik and prints them.

## See it in Opik

Open the **`dify-climbing-gym-assistant`** project.

- **Traces tab.** One `./demo.sh` gives **4 traces**, all named **`message`**, one per question.
- **Open a `message` trace.** The input is the full message list Dify sent: the system prompt with every gym fact,
  then the conversation so far. The output is the answer. Under it there is one **`llm`** span with the token usage:
  **459** tokens for the first question, growing to **694** for the fourth, because Dify resends the earlier turns
  each time.
- **Threads tab.** The four messages share one thread, keyed by Dify's conversation id, so you can read the whole
  chat as one transcript.
- **Metadata.** Each trace and span has `ls_model_name: gpt-4o-mini`, `ls_provider`, `conversation_id`,
  `message_id` and `end_user_id` (`demo-climber`), so a complaint from one member can be traced to the exact message.

In our final run, three answers matched the gym facts: the $59 student membership, the $15 belay check and the
$25 lead check, and the Tuesday 9:00-14:00 setting closure. The freeze answer did not: the model quoted the rule
correctly ("$10 per frozen month") but then said a six-week trip needs only **one** frozen month. An earlier run of
the same app gave the right answer (two months, $20). This is the kind of mistake the trace makes easy to explain:
the input shows the model had the right facts, so the fix belongs in the instructions, not the data.

## Run it yourself

You need Docker (about 10 images, several GB), `python3`, [`uv`](https://docs.astral.sh/uv/), an OpenAI key, and an
Opik instance (a [local Opik](https://www.comet.com/docs/opik/self-host/local_deployment) on
`http://localhost:5173` works).

1. In the repo root, copy `.env.example` to `.env` and set `OPENAI_API_KEY`. Keep
   `OPIK_URL_OVERRIDE=http://localhost:5173/api/` for a local Opik.
2. Start and configure Dify (the first run takes a few minutes):
   ```bash
   cd dify-climbing-gym-assistant
   ./setup.sh
   ```
3. Ask the four sample questions:
   ```bash
   ./demo.sh
   ```
4. Read the traces back, or open the project in the Opik UI:
   ```bash
   uv run --with opik python check_opik.py
   ```

Dify's UI is at `http://localhost:8090` (login `desk@basaltwall.example` / `BasaltWall-2026`, a local demo
account). Stop it with
`docker compose -f dify-docker/docker-compose.yaml --project-directory dify-docker down` (add `-v` to drop the data).

## Poke around

- **Change a fact.** In the Dify app, change the day-pass price from $22 to $25 and publish. Ask about it, then
  compare the system prompt in the old and new traces: the trace keeps the prompt that was actually used.
- **Ask something the facts don't cover** ("Do you have a sauna?"). The instructions tell the model to say so; check
  in the trace whether it did, or made something up.
- **Start a second conversation** by running `./demo.sh` again. It starts a new thread, and the first question's
  prompt is back to about 450 tokens.
- **Watch the turn-off switch.** Turn tracing off in the app's tracing settings in Dify, send a message, and check
  that no new trace arrives.

## Gotchas

- **The llm span has token usage but no cost.** *Symptom:* the cost column is empty, although `usage` holds prompt
  and completion tokens. *Cause:* Dify does not set the span's model and provider fields; the model name is only in
  metadata (`ls_model_name: gpt-4o-mini`), and the provider is the plugin id `langgenius/openai/openai`, which is
  not in Opik's price table. *Fix:* none in Dify itself. Read the tokens from the span and price them yourself if you
  need dollars.

- **An extra `generate_conversation_name` trace for every new conversation.** *Symptom:* four questions give five
  traces, and one of them is not a member's question. *Cause:* when a conversation starts, Dify makes a second
  model call to write a title for it, and its Opik provider traces that call too. *Fix:* send
  `"auto_generate_name": false` in the `/v1/chat-messages` request, as `demo.sh` does. If you keep auto-titles,
  filter the traces table on the name `message`.

## How it's put together

- `app/basalt-wall-front-desk.yml`: the Dify app (DSL): model, instructions with the gym facts, opening statement.
- `configure_dify.py`: headless Dify setup through the console API, including the Opik trace config (standard
  library only). Dify sends traces from inside its containers, so the script rewrites a `localhost` Opik URL to
  `host.docker.internal`.
- `setup.sh`: creates `dify-docker/.env` on first run, starts the stack, runs `configure_dify.py`.
- `demo.sh`: four questions in one conversation through `POST /v1/chat-messages`.
- `check_opik.py`: prints the project's traces, thread count, token usage and cost.
- `dify-docker/`: the upstream Dify 1.17.1 compose file, env template and nginx/sandbox config.
- `.env.example`: the variables this example reads from the repo-root `.env`.

---

*Built with [Opik](https://github.com/comet-ml/opik) · inspired by Opik's examples and
[documentation](https://www.comet.com/docs/opik/).*
