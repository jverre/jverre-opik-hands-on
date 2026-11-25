"""Offline tests: no provider key, no Opik server. Run with tracking disabled:

    env -u OPENAI_API_KEY OPIK_TRACK_DISABLE=true uv run pytest
"""

import json
from types import SimpleNamespace

import pytest

import main
from fields import normalize_postcode, normalize_tracking, parse_fields
from labels import EXPECTED, generate_labels


def test_normalizers():
    assert normalize_tracking("sp 4821-7730 19") == "SP4821773019"
    assert normalize_postcode(" sw1a   1aa ") == "SW1A 1AA"


def test_parse_fields_normalises_and_rounds():
    raw = json.dumps({"tracking_number": "NL-9923-4410-ab", "carrier": " Northline Express ",
                      "service_level": "Overnight", "sender_postcode": "sw1a 1aa",
                      "recipient_postcode": "m1 4bt", "weight_kg": 12.8001})
    out = parse_fields(raw)
    assert out["tracking_number"] == "NL99234410AB"
    assert out["carrier"] == "Northline Express"
    assert out["sender_postcode"] == "SW1A 1AA"
    assert out["weight_kg"] == 12.8


def test_parse_fields_rejects_missing_field():
    with pytest.raises(KeyError):
        parse_fields(json.dumps({"carrier": "x"}))


def test_generate_labels_writes_pngs(tmp_path, monkeypatch):
    monkeypatch.setattr("labels.DATA_DIR", tmp_path)
    paths = generate_labels(force=True)
    assert len(paths) == len(EXPECTED) == 6
    assert all(p.exists() and p.stat().st_size > 1000 for p in paths)


def test_suite_items_carry_truth_in_assertions_not_data():
    items = main.suite_items()
    assert len(items) == 6
    for item, lb in zip(items, EXPECTED):
        assert set(item["data"]) == {"image", "kind"}
        joined = " ".join(item["assertions"])
        assert lb.sender_postcode in joined and f"{lb.weight_kg}" in joined


def test_traced_extract_runs_with_stub_client(tmp_path, monkeypatch):
    """extract_label is @opik.track-ed; with tracking disabled it is a plain call."""
    reply = {"tracking_number": "sp 1", "carrier": "Swiftpost", "service_level": "Ground",
             "sender_postcode": "10115", "recipient_postcode": "80331", "weight_kg": 2.4}
    stub = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(
        create=lambda **kw: SimpleNamespace(choices=[SimpleNamespace(
            message=SimpleNamespace(content=json.dumps(reply)))]))))
    monkeypatch.setattr(main, "get_client", lambda: stub)
    image = tmp_path / "x.png"
    image.write_bytes(b"\x89PNG fake")
    assert main.extract_label(str(image))["tracking_number"] == "SP1"
