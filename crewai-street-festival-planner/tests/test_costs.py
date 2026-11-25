from types import SimpleNamespace as NS

from street_festival.costs import cost_by_agent, format_table
from street_festival.tracing import enable_tracing, flush


def span(id, parent, name, type="general", usage=None, cost=None):
    return NS(id=id, parent_span_id=parent, name=name, type=type, usage=usage, total_estimated_cost=cost)


def test_cost_is_grouped_under_the_agent_below_each_task():
    spans = [
        span("k", None, "kickoff"),
        span("t1", "k", "Task: Plan the site layout"),
        span("a1", "t1", "Logistics Planner"),
        span("f1", "a1", "Flow.kickoff_async"),
        span("l1", "f1", "chat_completion_create", "llm", {"prompt_tokens": 100, "completion_tokens": 20}, 0.001),
        span("t2", "k", "Task: Write the budget"),
        span("a2", "t2", "Budget Writer"),
        span("l2", "a2", "chat_completion_create", "llm", {"prompt_tokens": 50, "completion_tokens": 10}, 0.0005),
        span("l3", "a2", "chat_completion_create", "llm", {"prompt_tokens": 5, "completion_tokens": 5}, 0.0001),
    ]
    rows = {r.agent: r for r in cost_by_agent(spans)}
    assert rows["Logistics Planner"].prompt_tokens == 100
    assert rows["Budget Writer"].llm_calls == 2
    assert round(rows["Budget Writer"].cost_usd, 6) == 0.0006
    assert "total" in format_table(list(rows.values()))


def test_llm_span_outside_any_task_is_ignored():
    assert cost_by_agent([span("l", None, "chat_completion_create", "llm", {}, 1.0)]) == []


def test_missing_cost_counts_as_zero():
    spans = [span("t", None, "Task: X"), span("a", "t", "A"), span("l", "a", "c", "llm", None, None)]
    assert cost_by_agent(spans)[0].cost_usd == 0.0


def test_enabling_tracing_with_tracking_disabled_keeps_kickoff_callable(monkeypatch):
    from crewai import Crew

    from street_festival.crew import build_crew

    monkeypatch.setenv("OPENAI_API_KEY", "test-key-not-real")
    monkeypatch.setenv("OPIK_TRACK_DISABLE", "true")
    enable_tracing(build_crew())  # patches Crew.kickoff with Opik's tracking wrapper
    assert callable(Crew.kickoff)
    flush()  # nothing queued: must be a harmless no-op
