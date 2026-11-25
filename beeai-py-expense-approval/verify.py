"""Reads the project back from Opik and prints what the last run produced. `uv run verify.py`."""
import re

import opik

from expense_agent.tracing import PROJECT_NAME

client = opik.Opik()
traces = client.search_traces(project_name=PROJECT_NAME, max_results=50)
print(f"project {PROJECT_NAME}: {len(traces)} traces")
for t in traces:
    spans = sorted(
        client.search_spans(project_name=PROJECT_NAME, trace_id=t.id, max_results=500),
        key=lambda s: s.start_time,
    )
    shape = " > ".join(f"{s.type}:{s.name}" for s in spans)
    llm = [s for s in spans if s.type == "llm"]
    tokens = [(s.usage or {}).get("total", 0) for s in llm]
    providers = {s.provider for s in llm}
    cost = sum(s.total_estimated_cost or 0 for s in llm)
    report = re.search(r"Report (ER-\d+)", str(t.input)).group(1)
    verdict = re.search(r"Decision:\s*(\w+)", str(t.output)).group(1)
    agent = next(s for s in spans if s.name == "ReAct")
    iterations = agent.metadata.get("iteration")
    print(f"- {report} -> {verdict} (ReAct iterations in span metadata: {iterations})")
    print(f"  trace {t.id} spans={len(spans)} llm_tokens={tokens} providers={providers} llm_cost=${cost:.5f}")
    print(f"    {shape}")
