# optimizer-recipe-cuisine-classifier

[![Python](https://img.shields.io/badge/python-3.12+-blue?style=flat)](pyproject.toml)
[![opik](https://img.shields.io/badge/opik-2.3.3-2e8555?style=flat)](https://github.com/comet-ml/opik)
[![opik-optimizer](https://img.shields.io/badge/opik--optimizer-3.2.0-orange?style=flat)](https://github.com/comet-ml/opik)

**A recipe tagger that scores 0.2 gets its prompt rewritten by Opik's Agent Optimizer, and the climb to ~1.0 is a chart you can open.**

A food blog wants every recipe blurb tagged with one of five cuisines: `levantine`, `oaxacan`, `sichuan`, `nordic` or `west-african`. The first-draft prompt does name the five cuisines, yet the tags come back as friendly sentences ("This dish belongs to Levantine cuisine!") and a strict tag field rejects every one of them. You could keep poking at the wording by hand and eyeball a few replies. This example shows the measured alternative: a labeled dataset, a metric, and an optimizer that proposes new prompts and keeps whatever scores higher, with every trial recorded in Opik.

## What you'll build

Two small scripts around thirty invented menu descriptions (20 for training, 10 held out):

- `classifier.py` holds the loose baseline prompt and a traced `classify` call to gpt-4o-mini. Run it on its own to see the baseline score.
- `main.py` uploads the 20 training dishes as an Opik dataset, saves the baseline as version 1 of a prompt called `cuisine-classifier`, and runs `MetaPromptOptimizer` for at most six trials. It then scores the baseline and the winner on the 10 dishes the optimizer never saw, and saves the winner as version 2.

```
baseline prompt -> score on 20 dishes -> optimizer proposes 3 rewrites per round
      -> score each -> keep the best (<= 6 trials) -> check on 10 held-out dishes
```

A full run takes about a minute and a half and costs under a cent of gpt-4o-mini.

## See it in Opik

Open the Opik UI (http://localhost:5173 for a local install) and look in four places.

**Optimization runs.** Open the newest run on the dataset `recipe-cuisines-train`. The score chart has seven points: the baseline, then one per trial. In the run this README was written from, it read `0.2, 1.0, 0.95, 0.95, 1.0, 1.0, 0.95`. The baseline sits low because the replies are sentences; the first rewrite jumps to the ceiling by telling the model to answer with only the cuisine name. Click any trial to read the exact prompt it scored. Your numbers will differ a little, since gpt-4o-mini is sampled and the optimizer's rewrites vary. Two training dishes are deliberately tricky (plantain turnovers with black-bean paste, cured lamb on flatbread), which is why later trials hover around 0.9 to 0.95 instead of staying flat at 1.0.

**Project `optimizer-recipe-cuisine-classifier`, Traces tab.** One run leaves 144 traces: 140 `evaluation_task` traces (seven scoring passes times 20 dishes), two `optimization_algorithm` traces from the optimizer itself, and two `score_prompt` traces from the held-out check. Open the two `score_prompt` traces: each holds 10 `chat_completion_create` llm spans (one per held-out dish) and ends with an output of `0.0` for the baseline and `1.0` for the winner. In total the project holds 162 llm spans, all gpt-4o-mini, each with token usage and an estimated cost; they add up to about $0.003.

**Prompts.** `cuisine-classifier` has two versions. v1 is the baseline text, tagged `stage: baseline` in its metadata. v2 is the optimizer's winner, with `train_accuracy` and `held_out_accuracy` in its metadata. Your app can load v2 by name and roll back to v1 without a deploy.

**Datasets.** `recipe-cuisines-train` has 20 items with two columns, `description` and `label`.

## Run it yourself

1. Install [uv](https://docs.astral.sh/uv/) and have an Opik instance running (a local install listens on `http://localhost:5173`; see the [local deployment guide](https://www.comet.com/docs/opik/self-host/local_deployment)).
2. `cp .env.example .env`, then fill in `OPENAI_API_KEY`. The scripts also read a `.env` one folder up, so a shared repo-root file works too. For Opik Cloud, set `OPIK_API_KEY` and drop the URL override.
3. `uv sync`
4. Optional baseline check: `uv run classifier.py` prints one sample reply and the baseline accuracy on the 20 training dishes.
5. `uv run main.py` runs the optimization and prints the score curve, the held-out check, a link to the run and the winning prompt.
6. Offline tests: `env -u OPENAI_API_KEY OPIK_TRACK_DISABLE=true uv run pytest`

## Poke around

- Loosen the metric: in `classifier.py`, make `is_correct` accept any reply that contains the label. Watch the baseline jump and the optimizer have much less to do.
- Add a sixth cuisine (say `peruvian`) to `data.py` with a handful of dishes, add it to the baseline prompt, and see whether the optimizer keeps all six labels in its rewrites.
- Cut `MAX_TRIALS` to 2 in `main.py`. How much of the gain survives?
- Rewrite the first line of the `cuisine_exact_match` docstring to something vague like "Scores the reply." and re-run: the optimizer reads that line, so the quality of the rewrites changes.

## Gotchas we hit

**The run stops after one round with only a couple of trials, even though `max_trials=6`.** The optimizer's default `skip_perfect_score=True` ends the run at the first score of 0.95 or higher. If you want the full trial curve, construct it with `MetaPromptOptimizer(..., skip_perfect_score=False)`.

**The run link opens a page that looks empty.** `result.get_run_link()` is a session redirect (`/v1/session/redirect/optimizations/...`) that carries no project, so it lands in whichever project the UI showed last. Build the link yourself from `rest_client.optimizations.get_optimization_by_id(result.optimization_id).project_id`; `main.py` prints it as `optimization run`.

**`result.llm_cost_total` and `result.llm_token_usage_total` are `None`.** The optimizer did not fill them in for this run. Read the cost from Opik instead: sum `total_estimated_cost` over the project's llm spans.

**A prompt version shows no change description even though you passed `change_description`.** On `create_chat_prompt` it was stored for v1 only in one run and for neither version in another, so do not rely on it. `metadata=` persisted every time, which is why the accuracies live there.

## How it's put together

- `main.py`: dataset upload, the exact-match metric, the baseline library save, the bounded optimizer run, the held-out check and the winner's save.
- `classifier.py`: the loose baseline prompt, `classify` (an OpenAI client wrapped by `track_openai`), and `accuracy` (one `@opik.track` span per scoring pass).
- `data.py`: 30 invented recipe blurbs across five cuisines, split 20 train / 10 held out.
- `tests/test_logic.py`: normalization and the strict label match, the dataset split, the metric, trial-score flattening, the mustache conversion, and a traced `accuracy` call run against a stubbed client with tracking disabled.
- `tests/conftest.py`: switches Opik tracking off so unit tests stay offline.
- `pyproject.toml`, `.env.example`, `.gitignore`: dependencies (opik 2.3.3, opik-optimizer 3.2.0), config template, ignores.

---

*built with Opik · inspired by Opik's examples and documentation*
