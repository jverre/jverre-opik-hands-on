"""Turns the agent's final text into a structured Decision, so the app can act on it."""
import re
from dataclasses import dataclass

VERDICTS = ("approve", "needs_manager", "reject")


@dataclass
class Decision:
    verdict: str
    reason: str
    approver: str
    message: str


def _field(text: str, label: str) -> str:
    match = re.search(rf"^{label}:\s*(.+?)(?=^\w[\w ]*:|\Z)", text, re.MULTILINE | re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else ""


def parse_decision(text: str) -> Decision:
    verdict = _field(text, "Decision").lower().replace(" ", "_").replace("-", "_")
    if verdict not in VERDICTS:
        raise ValueError(f"Decision must be one of {VERDICTS}, got {verdict!r}")
    return Decision(verdict, _field(text, "Reason"), _field(text, "Approver"), _field(text, "Message"))
