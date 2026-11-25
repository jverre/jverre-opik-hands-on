"""Read the demo's traces back from Opik and check the cross-process lesson."""

import sys

import opik

from .tracing import OPIK_PROJECT


def summarize(spans: list) -> dict:
    """Pure helper: what the trace must show, computed from its spans."""
    names = [s.name for s in spans]
    attempts = [s for s in spans if s.name == "RunActivity:check_budget"]
    roots = [s for s in spans if s.parent_span_id is None]
    return {
        "span_count": len(spans),
        "single_root": len(roots) == 1 and roots[0].name.startswith("review:"),
        "budget_attempts": len(attempts),
        "failed_attempts": [s.error_info.message for s in attempts if s.error_info],
        "llm_spans": [s.name for s in spans if s.type == "llm"],
        "has_workflow_span": "RunWorkflow:GrantReview" in names,
    }


def main() -> int:
    client = opik.Opik(project_name=OPIK_PROJECT)
    # Flush so anything the demo just sent is queryable before we read it back.
    client.flush()
    traces = client.search_traces(project_name=OPIK_PROJECT, max_results=50)
    ok = bool(traces)
    for t in sorted(traces, key=lambda t: t.name):
        spans = client.search_spans(project_name=OPIK_PROJECT, trace_id=t.id, max_results=200)
        info = summarize(spans)
        good = (
            info["single_root"]
            and info["has_workflow_span"]
            and info["budget_attempts"] == 2
            and len(info["failed_attempts"]) == 1
            and len(info["llm_spans"]) == 2
        )
        ok &= good
        cost = t.total_estimated_cost
        print(f"{t.name}: {info['span_count']} spans, cost ${cost}, {info}  {'OK' if good else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
