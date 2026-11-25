# openai-vision-shipping-labels

[![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Opik](https://img.shields.io/badge/Opik-2.3-2f54eb?style=flat)](https://github.com/comet-ml/opik)
[![uv](https://img.shields.io/badge/setup-uv-DE5FE9?style=flat)](https://docs.astral.sh/uv/)

**A vision model reads six parcel labels. Opik keeps the pixels next to the answer, and a test suite tells you which reads you can't trust.**

When a vision model returns the wrong carrier or a digit-off tracking number, the
text of the trace tells you nothing: the evidence is the image. If that image
isn't stored with the trace, "why did it read SWIFTPOT?" turns into a hunt for
a file on somebody's disk. This example draws shipping labels at run time,
extracts typed fields from them with `gpt-4o-mini`, and makes each label an
attachment on its own Opik trace. A test suite then pins the true values and
records, honestly, where the model goes wrong.

## What you'll build

- `labels.py` draws six fictional labels with Pillow: four clean layouts
  (German, UK, US and Dutch postcodes; one prints its weight in pounds), one with
  a wet-ink smear across the tracking number, and one small, faded, sideways and
  skewed. Nothing is committed as an image; `main.py` regenerates them into `data/`.
- `main.py` sends each PNG to `gpt-4o-mini` with a strict JSON schema and gets
  back `tracking_number`, `carrier`, `service_level`, `sender_postcode`,
  `recipient_postcode` and `weight_kg`. `fields.py` normalises the result
  (tracking codes lose spaces and hyphens, postcodes are upper-cased).
- The same six labels become an Opik test suite. Four assertions per label carry the
  true values; three global assertions state format rules. Each label runs three times
  and passes if two runs pass.

## See it in Opik

Open the project **openai-vision-shipping-labels**. After one run it holds 24
traces: six `extract_label` traces from the plain pass over the labels and 18
`evaluation_task` traces from the suite (six labels times three runs).

Click any `extract_label` trace. Its tree is `extract_label` with a
`chat_completion_create` span nested inside, typed `llm`, carrying about 14,500 or
25,800 tokens (the image dominates the count, and the larger figure is the
tiling of the bigger labels) and roughly $0.002 to $0.004 of estimated cost.
Open the trace's **Attachments** tab and the label PNG is there, previewable, next to
the output. Every one of the 24 traces has its label attached, including the suite
ones. Click the smudged one (`label_05_smudged.png`) and you can see the smear the
model had to read through.

Now open **Experiments**, then `label-extraction-gpt-4o-mini` (18 runs). In the
verified run, 5 of 6 labels passed, and the failing one was the *clean*
`label_01_swiftpost.png`: the model read the header `SWIFTPOST` as `SWIFTPOT` in
two of its three runs, so "The carrier is Swiftpost" failed. The tracking number and
postcodes on that label were fine. The smudged and the rotated labels, the ones you'd
bet on failing, passed. Opik's own spans show the same thing from the other side:
`SWIFTPOT` (and once `SWIFTPRINT`) appears in the traces' outputs for both Swiftpost
labels. Which label fails can move between runs: in an earlier run the same carrier
misread failed the smudged Swiftpost label instead. That is why the suite runs
each label three times.

## Run it yourself

1. Install [uv](https://docs.astral.sh/uv/) and start a local Opik (default URL
   `http://localhost:5173`).
2. Copy `.env.example` to `.env` (here or at your repo root) and set `OPENAI_API_KEY`.
3. `uv sync`
4. `uv run main.py`

It takes about a minute and a half and costs around six cents. At the end it prints
the pass rate, each label's PASS/FAIL, and the experiment link.

Offline tests (no key, no Opik server):

```
env -u OPENAI_API_KEY OPIK_TRACK_DISABLE=true uv run pytest
```

## Poke around

- In `labels.py`, bump the smear's opacity or shrink the rotated label's `resize`
  and watch how the pass/fail pattern changes.
- Change `SYSTEM_PROMPT` to tell the model to spell the carrier exactly as printed,
  letter by letter, and re-run. Does `SWIFTPOT` go away?
- Set `runs_per_item` to 1 and see how much the pass/fail verdicts wobble between
  executions.
- List a trace's attachments from code with
  `client.rest_client.attachments.attachment_list(project_id=..., entity_type="trace", entity_id=..., path=base64(<api url>))`.

## Gotchas we hit

- **The suite suddenly has 12 items, or an item you edited shows up twice.**
  Test-suite items are de-duplicated by their content. Adding an `execution_policy`
  to items that were already inserted counts as a new item, so old and new copies
  both run. Fix: delete the suite (dataset) named like your project in the Opik UI,
  or use a new suite name, then run again.
- **A helper script's traces land in "Default Project".** Opik prints
  `No project name configured. Traces are being logged to "Default Project"`
  when a script creates `opik.Opik()` without a project. Set
  `OPIK_PROJECT_NAME=openai-vision-shipping-labels` (as `main.py` does) or pass
  `project_name=` to the client.

## How it's put together

- `labels.py`: draws the six labels and holds their ground truth (`EXPECTED`).
- `fields.py`: system prompt, JSON schema, and the normalising parser. No model, no Opik.
- `main.py`: `track_openai` client, the `@opik.track` extraction with the image attachment, suite and `run_tests`.
- `tests/test_labels.py`: normalisers, parser, label generation, suite items, and a traced call with a stub client and tracking off.
- `pyproject.toml`, `.env.example`, `.gitignore`: setup, with generated PNGs ignored.

*built with Opik · inspired by Opik's examples and documentation*
