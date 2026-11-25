"""An Opik test suite that checks extractions for invented values."""

from typing import Any

import opik

from tasting.agent import extract_note
from tasting.config import PROJECT_NAME
from tasting.corpus import load_notes

JUDGE_MODEL = "gpt-4o-mini"
EXPERIMENT_NAME = "tasting-notes-gpt-4o-mini"

# Rules every extraction must follow, written as plain sentences for the judge.
GLOBAL_ASSERTIONS = [
    "Every non-null value in the record is stated in the note, or is a direct "
    "normalisation of it (such as a currency symbol turned into an ISO code)",
    "score_100 is null unless the note gives a score on a 100-point scale",
    "grape is null unless the note itself names a grape (abbreviations such as "
    "'Cab Sauv' or 'chard' count as naming it)",
    "A value the note marks as uncertain is null rather than a confident guess",
]

# Expected values live in assertions, never in the item data, so the judge
# checks the output instead of copying answers from the input.
ASSERTIONS: dict[str, list[str]] = {
    "pauillac": [
        "The vintage is 2016, the region is Pauillac and the score is 94",
        "The price is 142 in USD and the grape is Cabernet Sauvignon",
    ],
    "chablis": [
        "The vintage is 2019, the grape is Chardonnay and the score is 91",
        "The price is 38 in EUR and the producer or wine mentions Veilleux",
    ],
    "sussex-bubbles": [
        "The vintage is null because the wine is non-vintage",
        "The price is null because the price tag was torn off",
        "The score is 89 and the producer is Halloran & Vane",
    ],
    "barolo": [
        "The score is null because the taster forgot to score the wine",
        "The grape is Nebbiolo, the vintage is 2015 and the price is 64 in GBP",
    ],
    "rioja": [
        "The vintage is null because the note cannot decide between 2010 and 2011",
        "The grape is Tempranillo and the price is 28 in EUR",
    ],
    "house-red": [
        "The score_100 is null: 7/10 must not be converted to 70",
        "The producer, vintage, region and grape are all null",
        "The price is 9 in USD",
    ],
}


def build_items() -> list[dict[str, Any]]:
    # Item data holds only the raw note, the same thing the agent receives.
    return [
        {"data": {"text": n["text"]}, "assertions": ASSERTIONS[n["id"]]} for n in load_notes()
    ]


def run_suite() -> Any:
    client = opik.Opik()
    # A test suite = items + plain-language assertions that an LLM judge checks.
    # Each judged run is an experiment; project_name files the suite under our project.
    # runs_per_item=3 absorbs judge/model flakiness: an item passes if 2 of 3 runs do.
    suite = client.get_or_create_test_suite(
        name=PROJECT_NAME,
        project_name=PROJECT_NAME,
        global_assertions=GLOBAL_ASSERTIONS,
        global_execution_policy={"runs_per_item": 3, "pass_threshold": 2},
    )
    suite.insert(build_items())  # identical items are deduplicated on re-runs

    def task(item: dict[str, Any]) -> dict[str, Any]:
        # extract_note is @opik.track'ed, so every suite run also leaves a trace.
        return {"input": item, "output": extract_note(item["text"])}

    result = opik.run_tests(
        test_suite=suite,
        task=task,
        experiment_name=EXPERIMENT_NAME,
        model=JUDGE_MODEL,
        worker_threads=4,
        generate_report=False,
    )
    client.flush()
    return result
