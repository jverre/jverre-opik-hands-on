import os

os.environ["OPIK_TRACK_DISABLE"] = "true"  # before opik is imported

import dspy

import factcheck


def test_parse_verdict_accepts_house_format():
    assert factcheck.parse_verdict("SUPPORTED | cites: F03") == ("SUPPORTED", "F03")
    assert factcheck.parse_verdict(" NOT ENOUGH INFO | cites: none\n") == ("NOT ENOUGH INFO", "none")


def test_parse_verdict_rejects_prose_and_extras():
    assert factcheck.parse_verdict("The claim is accurate.") is None
    assert factcheck.parse_verdict("SUPPORTED | cites: F03 because it says so") is None
    assert factcheck.parse_verdict("UNSUPPORTED") is None


def test_metric_needs_label_and_fact_id():
    ex = dspy.Example(label="REFUTED", cites="F08")
    ok = dspy.Prediction(verdict="REFUTED | cites: F08")
    assert factcheck.verdict_metric(ex, ok)
    assert not factcheck.verdict_metric(ex, dspy.Prediction(verdict="REFUTED | cites: F07"))
    assert not factcheck.verdict_metric(ex, dspy.Prediction(verdict="SUPPORTED | cites: F08"))


def test_data_is_consistent_with_the_fact_sheet():
    rows = factcheck.load_testset() + [
        {"label": e.label, "cites": e.cites} for e in factcheck.load_trainset()
    ]
    for row in rows:
        assert row["label"] in factcheck.LABELS
        if row["label"] == "NOT ENOUGH INFO":
            assert row["cites"] == "none"
        else:
            assert row["cites"] in factcheck.FACT_SHEET


def test_task_runs_offline_with_tracking_disabled():
    # make_task's function is @opik.track-ed; with tracking disabled it is a
    # plain call, so a stub program is all an offline test needs.
    seen = {}

    def stub_program(facts, claim):
        seen["claim"] = claim
        return dspy.Prediction(verdict="SUPPORTED | cites: F06")

    task = factcheck.make_task(stub_program)
    out = task({"claim": "Comet Brannigan-Oye returns every 61 years."})
    assert out == {"input": {"claim": seen["claim"]}, "output": "SUPPORTED | cites: F06"}
