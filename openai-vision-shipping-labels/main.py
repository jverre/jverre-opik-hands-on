"""Shipping-label field extraction with gpt-4o-mini vision, traced and tested with Opik.

Six label images are drawn locally (labels.py). Each one is sent to gpt-4o-mini,
which returns six typed fields. Every extraction is one Opik trace with the
label PNG attached, and an Opik test suite then checks each output against
plain-language assertions that hold the true values.
"""

import base64
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

PROJECT_NAME = "openai-vision-shipping-labels"
HERE = Path(__file__).parent

# Secrets and the Opik URL come from the repo-root .env (a local .env works too).
load_dotenv(HERE.parent / ".env")
load_dotenv(HERE / ".env")
os.environ.pop("OPENAI_BASE_URL", None)  # this example talks to the public OpenAI API
# Every trace, dataset and experiment in this file lands in this Opik project.
os.environ["OPIK_PROJECT_NAME"] = PROJECT_NAME

import opik  # noqa: E402
from openai import OpenAI  # noqa: E402
from opik import Attachment, opik_context  # noqa: E402
from opik.integrations.openai import track_openai  # noqa: E402

from fields import FIELDS_SCHEMA, SYSTEM_PROMPT, parse_fields  # noqa: E402
from labels import EXPECTED, Label, generate_labels  # noqa: E402

MODEL = "gpt-4o-mini"
_client: Any = None


def get_client() -> Any:
    global _client
    if _client is None:
        # track_openai wraps the client: each completion becomes an llm span with
        # token usage and cost (image tokens included) under the calling trace.
        _client = track_openai(OpenAI(), project_name=PROJECT_NAME)
    return _client


# @opik.track opens the trace: input is the image path, output is the parsed fields.
# Without it the completion would be a lone span with no label attached.
@opik.track(project_name=PROJECT_NAME, name="extract_label")
def extract_label(image_path: str) -> dict[str, Any]:
    """One extraction: label image in, six normalised fields out."""
    path = Path(image_path)
    image_b64 = base64.b64encode(path.read_bytes()).decode()

    # Attaches the PNG to this trace: the Attachments tab shows the exact pixels the model saw.
    opik_context.update_current_trace(
        attachments=[Attachment(data=str(path), content_type="image/png", file_name=path.name)]
    )

    response = get_client().chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": [
                {"type": "text", "text": "Extract the fields from this shipping label."},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}", "detail": "high"}},
            ]},
        ],
        response_format={"type": "json_schema",
                         "json_schema": {"name": "label_fields", "strict": True, "schema": FIELDS_SCHEMA}},
    )
    return parse_fields(response.choices[0].message.content)


# --- The test suite: format rules for every label, true values per label -----------

# Judged from the output alone, for every item.
GLOBAL_ASSERTIONS = [
    "All six fields are present and none is null or empty",
    "The tracking number contains only letters and digits, with no spaces or hyphens",
    "weight_kg is a plausible parcel weight in kilograms (a positive number under 70)",
]


def assertions_for(lb: Label) -> list[str]:
    """Plain-language assertions carrying the ground truth for one label."""
    return [
        f"The carrier is {lb.carrier} and the service level is {lb.service_level}",
        f"The tracking number is {lb.tracking_number.replace(' ', '').replace('-', '')} "
        "(exactly these characters, in this order)",
        f"The sender postcode is {lb.sender_postcode} and the recipient postcode is {lb.recipient_postcode}",
        f"The weight is {lb.weight_kg} kg (a difference under 0.05 kg is fine)",
    ]


def suite_items() -> list[dict[str, Any]]:
    # `data` holds only the image path and a description; the answers live in
    # the assertions, so the judge compares output to truth rather than echoing the input.
    return [
        {
            "data": {"image": f"data/{lb.file}", "kind": lb.kind},
            "assertions": assertions_for(lb),
            # Run each label 3 times and pass if 2 of 3 runs pass: smooths over
            # one-off judge slips and one-off misreads, and shows up as 3 runs per row.
            "execution_policy": {"runs_per_item": 3, "pass_threshold": 2},
        }
        for lb in EXPECTED
    ]


def main() -> None:
    generate_labels()  # redraw the PNGs if data/ is empty (they are git-ignored)
    items = suite_items()

    print(f"Extracting fields from {len(items)} label images with {MODEL}...\n")
    for item in items:
        fields = extract_label(str(HERE / item["data"]["image"]))
        print(f"  {item['data']['image']}\n    -> {fields}\n")

    client = opik.Opik()
    # A test suite is a dataset plus LLM-judged assertions; global ones apply to every item.
    suite = client.get_or_create_test_suite(
        name=PROJECT_NAME, project_name=PROJECT_NAME, global_assertions=GLOBAL_ASSERTIONS
    )
    suite.insert(items)

    def extraction_task(item: dict[str, Any]) -> dict[str, Any]:
        return {"input": item, "output": extract_label(str(HERE / item["image"]))}

    # run_tests creates an experiment: 6 labels x 3 runs, every run's assertions judged pass/fail
    # by an LLM judge; each run is also an evaluation_task trace in this project.
    result = opik.run_tests(
        test_suite=suite,
        task=extraction_task,
        experiment_name="label-extraction-gpt-4o-mini",
        worker_threads=3,
        generate_report=False,
    )

    print(f"\nPass rate: {result.pass_rate:.0%} ({result.items_passed}/{result.items_total} labels)")
    for item_result in result.item_results.values():
        image = item_result.test_results[0].test_case.task_output["input"]["image"]
        print(f"  [{'PASS' if item_result.passed else 'FAIL'}] {image}")
    print(f"\nExperiment: {result.experiment_name} ({result.experiment_url})")

    # Traces are sent from a background thread; flush so none are lost at exit.
    opik.flush_tracker()
    client.flush()


if __name__ == "__main__":
    main()
