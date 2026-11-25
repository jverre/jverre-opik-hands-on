import pytest

from expense_agent.decision import parse_decision

ANSWER = """Decision: needs_manager
Reason: Over the USD 60 per person limit.
Still the reason.
Approver: Marcus Lindqvist, marcus.lindqvist@harborpine.example
Message: Hi Dana, Marcus will review it."""


def test_parse_decision_reads_all_four_fields():
    d = parse_decision(ANSWER)
    assert d.verdict == "needs_manager"
    assert d.reason == "Over the USD 60 per person limit.\nStill the reason."
    assert d.approver.startswith("Marcus Lindqvist")
    assert d.message.startswith("Hi Dana")


def test_parse_decision_tolerates_spacing_and_case():
    assert parse_decision("Decision: Needs Manager  \nReason: x").verdict == "needs_manager"


def test_parse_decision_rejects_unknown_verdict():
    with pytest.raises(ValueError):
        parse_decision("Decision: maybe\nReason: x")
