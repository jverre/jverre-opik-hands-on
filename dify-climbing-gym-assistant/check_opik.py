"""Read the Dify traces back from Opik and print what landed.

Run: uv run --with opik python check_opik.py
Reads OPIK_URL_OVERRIDE / OPIK_WORKSPACE / OPIK_API_KEY from the shell or the repo-root .env.
"""

import os
import pathlib

# Load the repo-root .env without extra dependencies (shell values win).
env_file = pathlib.Path(__file__).resolve().parent.parent / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())

import opik  # noqa: E402  (imported after the .env is loaded so the SDK sees the URL)

PROJECT = "dify-climbing-gym-assistant"

# Opik: the client reads the Opik URL and workspace from the environment set above.
client = opik.Opik(project_name=PROJECT)
traces = sorted(client.search_traces(project_name=PROJECT, max_results=200), key=lambda t: t.start_time)
threads = {t.thread_id for t in traces if t.thread_id}
print(f"project {PROJECT}: {len(traces)} traces, {len(threads)} thread(s)")
for trace in traces:
    # Opik: Dify writes one trace per chat message, with the model call as a child llm span.
    spans = client.search_spans(project_name=PROJECT, trace_id=trace.id, max_results=20)
    llm = next((s for s in spans if s.type == "llm"), None)
    usage = (llm.usage or {}) if llm else {}
    model = (llm.metadata or {}).get("ls_model_name") if llm else None
    print(f"- {trace.name:28} tokens={usage.get('total_tokens', '-'):>4} model={model} "
          f"cost={llm.total_estimated_cost if llm else None}  out={str(trace.output)[:60]!r}")
