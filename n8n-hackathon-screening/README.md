# n8n-hackathon-screening

**A no-code n8n workflow that screens hackathon submissions with gpt-4o-mini, traced into Opik without adding a single node.**

![n8n](https://img.shields.io/badge/n8n-2.41.7-EA4B71) ![n8n--observability](https://img.shields.io/badge/n8n--observability-1.0.3-blue) ![runs in](https://img.shields.io/badge/runs%20in-Docker-2496ED)

Driftwood Hack is a fictional weekend hackathon for "tools for coastal towns". Submissions arrive on a webhook, an
OpenAI node scores each one for originality, feasibility and theme fit, and the workflow answers with
`shortlist`, `maybe` or `decline` plus a line of feedback for the team.

The organisers built that in n8n's canvas. When a team asks "why were we declined?", the answer is buried in an
execution log nobody keeps. This example sends every execution to Opik as a trace, so the exact submission, the
prompt the node used and the model's verdict are one click away, and nobody had to change the workflow to get it.

## What you'll build

- An n8n instance in Docker with the [`n8n-observability`](https://github.com/comet-ml/n8n-observability) hooks
  installed in the image. That is the whole integration: no Opik nodes, no code inside the workflow.
- A four-node workflow, imported through n8n's REST API by `setup.sh`:
  `Submission webhook` → `Screen submission (gpt-4o-mini)` → `Shape the verdict` → `Respond`.
- `demo.sh`, which posts three sample submissions from `data/submissions.json`.

## See it in Opik

Open the **`n8n-hackathon-screening`** project. After one `./demo.sh` you get **3 traces**, all named
**`Hackathon screening`** (the workflow name), one per submission.

Open any trace. The tree has **5 spans**: the workflow span at the root, then one span per node in the order n8n
ran them: `Submission webhook`, `Screen submission (gpt-4o-mini)`, `Shape the verdict`, `Respond`.

- Click **`Screen submission (gpt-4o-mini)`**. Its input panel holds the node's configuration as flat attributes:
  `n8n.node.parameters.modelId.value` is `gpt-4o-mini`, `n8n.node.parameters.messages.values.0.content` is the full
  judging rubric, and `n8n.node.output` is the model's JSON verdict with the three scores.
- Click **`Submission webhook`**. `n8n.node.output` shows the exact request body the team sent.
- Click **`Respond`**. `n8n.node.output` is what the team got back.

In our run, *Low Tide Labs* (a tide-warning bot) and *Gull Patrol* (a beach-litter map) came back `maybe` with
theme fit 5 but feasibility 3, and *Northwind Systems* (an existing commercial product) was `decline` with
originality 1. The reason sentence for each sits next to the scores, so you can check whether the rubric did what
the organisers meant.

## Run it yourself

You need Docker, `curl`, `python3`, an OpenAI key, and an Opik instance (a
[local Opik](https://www.comet.com/docs/opik/self-host/local_deployment) on `http://localhost:5173` works).

1. In the repo root, copy `.env.example` to `.env` and set `OPENAI_API_KEY`. Leave `OPIK_URL_OVERRIDE` at
   `http://localhost:5173/api/` for a local Opik.
2. Start n8n, create the owner account, the OpenAI credential and the workflow:
   ```bash
   cd n8n-hackathon-screening
   ./setup.sh
   ```
3. Send the three sample submissions:
   ```bash
   ./demo.sh
   ```
4. Open Opik and pick the `n8n-hackathon-screening` project.

The n8n UI is at `http://localhost:5678` (login `judge@example.com` / `Hackathon-demo-1`, a local demo account).
Stop everything with `docker compose down` (add `-v` to also drop n8n's data volume).

## Poke around

- **Change the rubric in the n8n canvas** (for example, make feasibility count double), run `./demo.sh` again and
  compare the `messages.values.0.content` attribute between an old and a new trace. The trace keeps the prompt that
  was actually used for that execution.
- **Send your own submission:**
  `curl -X POST localhost:5678/webhook/hackathon-screening -H 'Content-Type: application/json' -d '{"team":"…","project":"…","pitch":"…","prior_work":"…"}'`.
  Try an empty pitch and see which span shows the problem.
- **Break an expression** in `Shape the verdict` (for example, rename `decision` to `verdict` in the OpenAI node's
  instructions). The `Shape the verdict` span shows empty fields while the `Screen submission` span still has the
  model output, so you can see which node lost the data.
- **Point it at another project:** edit `PROJECT` in `setup.sh` and run it again; new executions land in the new
  project.

## Gotchas

- **The OpenAI node's span has no token usage and no cost.** *Symptom:* the `Screen submission (gpt-4o-mini)` span
  is type `general`, and its usage and cost columns are empty. *Cause:* with n8n 2.41.7 and n8n-observability 1.0.3
  the exported spans carry `n8n.*` attributes only, with no `gen_ai.*` model or usage attributes, so Opik has
  nothing to price. *Fix:* none inside n8n today. Read the model from `n8n.node.parameters.modelId.value`, and if
  you need cost, call the model from a small service that you trace with an Opik SDK integration.
- **The trace's Output column is empty.** *Symptom:* the traces table shows the workflow name and input but no
  output. *Cause:* the root span only gets `n8n.workflow.*` attributes; each node's result is stored on its own span.
  *Fix:* open the `Respond` span: its `n8n.node.output` is the response the webhook sent.
- **Node input and output are strings, not JSON.** *Symptom:* `n8n.node.output` reads like
  `[{'team': 'Low Tide Labs', ...}]`, with single quotes, so Opik shows it as text and you can't expand it.
  *Cause:* the hooks write node data as a string attribute. *Fix:* read it as text, or search inside it with the
  traces search box; filtering on individual fields is not possible.

## How it's put together

- `Dockerfile`: n8n 2.41.7 plus `n8n-observability`, enabled through `EXTERNAL_HOOK_FILES`.
- `docker-compose.yml`: the n8n service; the OTLP endpoint and the `Comet-Workspace` / `projectName` headers that
  route traces into Opik.
- `setup.sh`: derives the OTLP endpoint from `OPIK_URL_OVERRIDE`, starts n8n, claims it, creates the OpenAI
  credential from the environment and imports and activates the workflow (safe to re-run).
- `demo.sh`: posts each submission in `data/submissions.json` to the webhook.
- `workflow/hackathon-screening.json`: the four-node workflow; the credential id is filled in at import time.
- `data/submissions.json`: three fictional submissions.
- `.env.example`: the variables this example reads from the repo-root `.env`.

---

*Built with [Opik](https://github.com/comet-ml/opik) · inspired by Opik's examples and
[documentation](https://www.comet.com/docs/opik/).*
