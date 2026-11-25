"""Offline tests: no provider keys, no Opik, no Temporal server."""

import asyncio
from types import SimpleNamespace

import pytest

from grant_review import llm
from grant_review.budget import check_budget
from grant_review.check_trace import summarize
from grant_review.config import get_application, load_applications, load_rules
from grant_review.tracing import _otlp_url, llm_span


def test_every_application_has_budget_lines():
    apps = load_applications()
    assert len(apps) == 3
    assert all(a["budget"] for a in apps)


def test_budget_ok_when_lines_add_up():
    assert check_budget(get_application("GR-101")) == {"line_total": 3200, "ok": True, "problems": []}


def test_budget_flags_mismatch_and_cap():
    assert "4300" in check_budget(get_application("GR-102"))["problems"][0]
    problems = check_budget(get_application("GR-103"))["problems"]
    assert any("maximum award" in p for p in problems)


def test_unknown_application():
    with pytest.raises(KeyError):
        get_application("GR-999")
    assert "5,000" in load_rules()


def test_otlp_url_from_opik_api_base(monkeypatch):
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)
    monkeypatch.setenv("OPIK_URL_OVERRIDE", "http://example:5173/api/")
    assert _otlp_url() == "http://example:5173/api/v1/private/otel/v1/traces"


def test_summarize_counts_attempts():
    def span(name, parent=None, error=None, type="general"):
        return SimpleNamespace(
            name=name, parent_span_id=parent, type=type,
            error_info=SimpleNamespace(message=error) if error else None,
        )

    spans = [
        span("review:GR-1"),
        span("RunWorkflow:GrantReview", "a"),
        span("RunActivity:check_budget", "a", error="503"),
        span("RunActivity:check_budget", "a"),
        span("reviewer-summary", "a", type="llm"),
    ]
    info = summarize(spans)
    assert info["single_root"] and info["budget_attempts"] == 2
    assert info["failed_attempts"] == ["503"] and info["llm_spans"] == ["reviewer-summary"]


def test_traced_llm_call_with_stubbed_client(monkeypatch):
    # The span wrapper is plain OpenTelemetry: with no exporter configured it is a no-op,
    # so the model-backed helper still runs and returns parsed output.
    class FakeCompletions:
        async def create(self, **kwargs):
            msg = SimpleNamespace(content='{"eligible": true, "reasons": []}')
            usage = SimpleNamespace(prompt_tokens=10, completion_tokens=5)
            return SimpleNamespace(choices=[SimpleNamespace(message=msg)], usage=usage, model="stub")

    fake = SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions()))
    monkeypatch.setattr(llm, "AsyncOpenAI", lambda: fake)
    result, _ = asyncio.run(llm.chat_json("eligibility-check", "sys", "user"))
    assert result["eligible"] is True
    with llm_span("x", "s", "u") as span:
        assert span is not None
