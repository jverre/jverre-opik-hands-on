"""A DSPy claim-checking program for a fictional observatory fact sheet.

Verdicts must follow the desk's house format: "<LABEL> | cites: <FACT-ID>".
That convention is not written in the signature; it only lives in worked
examples, which is what DSPy compilation is for.
"""

import json
import os
import pathlib
import re

import dotenv
import dspy

HERE = pathlib.Path(__file__).parent
MODEL = "openai/gpt-4o-mini"
LABELS = ("SUPPORTED", "REFUTED", "NOT ENOUGH INFO")

# Provider keys come from the nearest .env up the tree (the repo root, usually).
for _parent in HERE.parents:
    if (_parent / ".env").exists():
        dotenv.load_dotenv(_parent / ".env")
        break
# Use the public API even if a shell exports a proxy base URL.
for _var in ("OPENAI_BASE_URL", "OPENAI_API_BASE"):
    os.environ.pop(_var, None)

FACT_SHEET = (HERE / "data" / "factsheet.txt").read_text()


class CheckClaim(dspy.Signature):
    """Check the claim against the observatory fact sheet."""

    facts: str = dspy.InputField(desc="the observatory fact sheet")
    claim: str = dspy.InputField()
    verdict: str = dspy.OutputField()


def build_program() -> dspy.Module:
    # Nothing here mentions the house format: the raw program answers in prose.
    return dspy.ChainOfThought(CheckClaim)


VERDICT = re.compile(r"^(SUPPORTED|REFUTED|NOT ENOUGH INFO) \| cites: (F\d{2}|none)$")


def parse_verdict(text: str) -> tuple[str, str] | None:
    """Return (label, cited fact id or 'none'), or None if off-format."""
    match = VERDICT.match(text.strip())
    return (match.group(1), match.group(2)) if match else None


def verdict_metric(example: dspy.Example, prediction, trace=None) -> bool:
    """Compile-time metric: exact house format, right label, right fact id."""
    return parse_verdict(prediction.verdict) == (example.label, example.cites)


def _load(name: str) -> list[dict]:
    return json.loads((HERE / "data" / name).read_text())


def load_trainset() -> list[dspy.Example]:
    return [
        dspy.Example(
            facts=FACT_SHEET, claim=row["claim"], label=row["label"],
            cites=row["cites"], verdict=f'{row["label"]} | cites: {row["cites"]}',
        ).with_inputs("facts", "claim")
        for row in _load("train.json")
    ]


def load_testset() -> list[dict]:
    return _load("test.json")


def configure_lm() -> dspy.LM:
    lm = dspy.LM(MODEL, cache=False)
    dspy.configure(lm=lm)
    return lm


def compile_program(program: dspy.Module) -> dspy.Module:
    """BootstrapFewShot: keep teacher attempts that pass the metric as demos."""
    optimizer = dspy.BootstrapFewShot(
        metric=verdict_metric, max_bootstrapped_demos=5,
        max_labeled_demos=5, max_rounds=1,
    )
    return optimizer.compile(program, trainset=load_trainset())
