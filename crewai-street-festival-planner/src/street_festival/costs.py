"""Read a finished trace back from Opik and total tokens and dollars per agent."""

from dataclasses import dataclass
from typing import Any

import opik

from street_festival.tracing import PROJECT_NAME

TASK_PREFIX = "Task: "


@dataclass
class AgentCost:
    agent: str
    task: str
    llm_calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0


def cost_by_agent(spans: list[Any]) -> list[AgentCost]:
    """Group llm spans under the agent span that sits directly below each 'Task: ...' span.

    `spans` are Opik span objects (or anything with id, parent_span_id, name, type,
    usage and total_estimated_cost attributes).
    """
    by_id = {s.id: s for s in spans}
    rows: dict[str, AgentCost] = {}
    for span in spans:
        if span.type != "llm":
            continue
        node, chain = span, []
        while node.parent_span_id and node.parent_span_id in by_id:
            node = by_id[node.parent_span_id]
            chain.append(node)
        agent = task = None
        for child, parent in zip(chain, chain[1:]):
            if parent.name.startswith(TASK_PREFIX):
                agent, task = child.name, parent.name.removeprefix(TASK_PREFIX)
                break
        if agent is None:
            continue
        row = rows.setdefault(agent, AgentCost(agent, task))
        usage = span.usage or {}
        row.llm_calls += 1
        row.prompt_tokens += usage.get("prompt_tokens", 0)
        row.completion_tokens += usage.get("completion_tokens", 0)
        row.cost_usd += span.total_estimated_cost or 0.0
    return list(rows.values())


def format_table(rows: list[AgentCost]) -> str:
    lines = [f"{'agent':<20} {'task':<22} {'calls':>5} {'prompt':>7} {'compl.':>7} {'cost (USD)':>11}"]
    for r in rows:
        lines.append(
            f"{r.agent:<20} {r.task:<22} {r.llm_calls:>5} {r.prompt_tokens:>7} "
            f"{r.completion_tokens:>7} {r.cost_usd:>11.6f}"
        )
    lines.append(f"{'total':<20} {'':<22} {sum(r.llm_calls for r in rows):>5} "
                 f"{sum(r.prompt_tokens for r in rows):>7} {sum(r.completion_tokens for r in rows):>7} "
                 f"{sum(r.cost_usd for r in rows):>11.6f}")
    return "\n".join(lines)


def latest_trace_report(project_name: str = PROJECT_NAME) -> str:
    client = opik.Opik(project_name=project_name)
    # Opik computes tokens and cost on each llm span; here we only read them back and add them up.
    traces = client.search_traces(project_name=project_name, max_results=50)
    if not traces:
        return f"No traces in project {project_name!r} yet. Run `festival plan` first."
    trace = max(traces, key=lambda t: t.start_time)
    spans = client.search_spans(project_name=project_name, trace_id=trace.id, max_results=1000)
    return f"Trace {trace.id}\n" + format_table(cost_by_agent(spans))
