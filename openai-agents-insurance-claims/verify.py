"""Read the project back from Opik and print what the demo run produced.

Run after `uv run main.py`:  uv run verify.py
"""

import os
from collections import Counter
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

import opik

PROJECT = "openai-agents-insurance-claims"


def main() -> None:
    # The same client the SDK uses for logging also queries the REST API.
    client = opik.Opik(project_name=PROJECT)
    client.flush()
    traces = client.search_traces(project_name=PROJECT, max_results=100)
    print(f"project {PROJECT!r}: {len(traces)} traces")

    threads = Counter(t.thread_id for t in traces)
    print(f"threads: {dict(threads)}")

    for trace in sorted(traces, key=lambda t: t.start_time):
        spans = client.search_spans(project_name=PROJECT, trace_id=trace.id, max_results=200)
        types = Counter(s.type for s in spans)
        tools = [s.name for s in spans if s.type == "tool"]
        handoffs = [s.name for s in spans if s.name.startswith("Handoff")]
        cost = sum(s.total_estimated_cost or 0 for s in spans)
        tokens = sum((s.usage or {}).get("total_tokens", 0) for s in spans)
        print(f"- {trace.thread_id}: {len(spans)} spans {dict(types)} tokens={tokens} cost=${cost:.5f}")
        print(f"    tools={tools} handoffs={handoffs}")


if __name__ == "__main__":
    main()
