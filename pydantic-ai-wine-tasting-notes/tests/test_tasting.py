"""Offline tests: no provider keys and no Opik server needed."""

import json

import pytest
from pydantic_ai.models.test import TestModel

from tasting import agent as agent_module
from tasting.cli import build_parser
from tasting.corpus import get_note, load_notes
from tasting.schema import TastingNote
from tasting.suite import ASSERTIONS, GLOBAL_ASSERTIONS, build_items
from tasting.telemetry import _otlp_endpoint


def test_every_note_has_assertions():
    ids = [n["id"] for n in load_notes()]
    assert set(ids) == set(ASSERTIONS)
    assert all(len(ASSERTIONS[i]) >= 2 for i in ids)


def test_item_data_never_contains_expected_values():
    # The judge must read assertions, not answers: item data is only the text.
    for item in build_items():
        assert list(item["data"]) == ["text"]
    assert len(GLOBAL_ASSERTIONS) >= 3


def test_get_note_unknown_id():
    with pytest.raises(KeyError):
        get_note("nope")


def test_schema_defaults_to_nulls():
    note = TastingNote()
    assert note.vintage is None and note.score_100 is None and note.descriptors == []


def test_traced_extract_note_runs_with_stub_model(monkeypatch):
    # extract_note is wrapped by @opik.track; with OPIK_TRACK_DISABLE=true the
    # decorator is a pass-through, so it unit-tests like a plain function.
    stub = TestModel(custom_output_args={"wine": "Test Cuvee", "vintage": 2020})
    agent_module.get_agent.cache_clear()
    monkeypatch.setattr(agent_module, "MODEL", stub)
    out = agent_module.extract_note("2020 Test Cuvee")
    assert out["wine"] == "Test Cuvee" and out["vintage"] == 2020
    assert out["score_100"] is None
    agent_module.get_agent.cache_clear()


def test_otlp_endpoint_from_env(monkeypatch):
    monkeypatch.setenv("OPIK_URL_OVERRIDE", "http://example:9/api/")
    assert _otlp_endpoint() == "http://example:9/api/v1/private/otel"
    monkeypatch.delenv("OPIK_URL_OVERRIDE")
    assert _otlp_endpoint() == "http://localhost:5173/api/v1/private/otel"


def test_cli_parses_commands():
    p = build_parser()
    assert p.parse_args(["extract", "--id", "barolo"]).id == "barolo"
    assert p.parse_args(["suite"]).command == "suite"
    assert json.loads(json.dumps(load_notes()))
