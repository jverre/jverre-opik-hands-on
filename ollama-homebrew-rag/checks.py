"""Cheap, deterministic checks for the handbook answers (no judge model needed)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Case:
    question: str
    expected_fact: str  # a string the correct answer must contain
    expected_source: str  # the handbook file that holds that fact


CASES = [
    Case(
        "What temperature should I mash at for a dry, crisp saison?",
        "63",
        "mashing.md",
    ),
    Case(
        "How should I add hops for a hazy IPA whirlpool?",
        "80",
        "hops.md",
    ),
    Case(
        "My fermentation is stuck at 1.030. What should I do first?",
        "temperature",
        "fermentation-troubleshooting.md",
    ),
    Case(
        "How long does the sanitizer need to touch a surface?",
        "2 minutes",
        "sanitation.md",
    ),
]


def answer_has_fact(answer: str, expected_fact: str) -> float:
    """1.0 when the answer states the handbook's fact, else 0.0."""
    return 1.0 if expected_fact.lower() in answer.lower() else 0.0
