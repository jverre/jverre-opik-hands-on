"""Offline tests: a stub replaces the OpenAI client, and Opik tracking is disabled."""

import json
from types import SimpleNamespace

import opik
import pipeline


class StubOpenAI:
    """Mimics client.chat.completions.create() with a canned JSON reply."""

    def __init__(self, entities):
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))
        self._reply = json.dumps({"entities": entities})

    def _create(self, **_kwargs):
        return SimpleNamespace(
            model="gpt-4o-mini-stub",
            choices=[SimpleNamespace(message=SimpleNamespace(content=self._reply))],
            usage=SimpleNamespace(prompt_tokens=10, completion_tokens=5, total_tokens=15),
        )


def test_regex_scan_finds_structured_ids():
    text = "Mail a@example.com, call (555) 010-4417, SSN 912-45-6789, card 4111 1111 1111 1111."
    types = {e["type"] for e in pipeline.regex_scan(text)}
    assert types == {"EMAIL", "PHONE", "SSN", "CARD"}


def test_parse_entities_ignores_bad_json_and_unknown_types():
    assert pipeline.parse_entities("not json") == []
    raw = json.dumps({"entities": [{"text": "Ada", "type": "PERSON"}, {"text": "x", "type": "COLOR"}]})
    assert [e["text"] for e in pipeline.parse_entities(raw)] == ["Ada"]


def test_merge_drops_hallucinated_entities():
    llm = [{"text": "Ada Lovelace", "type": "PERSON", "source": "llm"},
           {"text": "Grace Hopper", "type": "PERSON", "source": "llm"}]
    merged = pipeline.merge_entities("Ada Lovelace wrote.", llm)
    assert [e["text"] for e in merged] == ["Ada Lovelace"]


def test_redact_replaces_longest_first():
    ents = pipeline.classify([{"text": "Ada", "type": "PERSON"}, {"text": "Ada Lovelace", "type": "PERSON"}])
    out, mapping = pipeline.redact("Ada Lovelace met Ada.", ents)
    assert "Ada" not in out and set(mapping) == {"Ada", "Ada Lovelace"}


def test_audit_reports_a_leak():
    report = pipeline.audit("Hello Marisol, [PERSON_1] here.", [], ["Marisol", "Marisol Venkataraman"])
    assert report["leak_free"] is False and "Marisol" in report["leaked"]
    assert report["recall"] == 0.5


def test_traced_pipeline_runs_with_tracking_disabled():
    # With OPIK_TRACK_DISABLE=true the Opik client records nothing, but the same
    # trace/span calls run unchanged, so the pipeline's output can be unit-tested.
    doc = {"id": "t1", "title": "t", "text": "Ada Lovelace: ada@example.com", "expected": ["Ada Lovelace", "ada@example.com"]}
    stub = StubOpenAI([{"text": "Ada Lovelace", "type": "PERSON"}])
    result = pipeline.process_document(stub, opik.Opik(project_name="tests"), doc)
    assert result["redacted"] == "[PERSON_1]: [EMAIL_1]"
    assert result["leak_free"] is True and result["recall"] == 1.0


def test_failed_model_call_still_raises_with_tracking_disabled():
    class Boom:
        chat = SimpleNamespace(completions=SimpleNamespace(create=lambda **_: (_ for _ in ()).throw(RuntimeError("down"))))

    doc = {"id": "t2", "title": "t", "text": "nothing here", "expected": []}
    try:
        pipeline.process_document(Boom(), opik.Opik(project_name="tests"), doc)
    except RuntimeError as exc:
        assert str(exc) == "down"
    else:
        raise AssertionError("expected the model error to propagate")
