from expense_agent import tracing


def test_otlp_url_defaults_to_local_opik(monkeypatch):
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)
    monkeypatch.delenv("OPIK_URL_OVERRIDE", raising=False)
    assert tracing.opik_otlp_traces_url() == "http://localhost:5173/api/v1/private/otel/v1/traces"


def test_otlp_url_follows_opik_url_override(monkeypatch):
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)
    monkeypatch.setenv("OPIK_URL_OVERRIDE", "http://opik.internal/api/")
    assert tracing.opik_otlp_traces_url() == "http://opik.internal/api/v1/private/otel/v1/traces"


def test_headers_route_to_project_and_only_send_key_when_set(monkeypatch):
    monkeypatch.delenv("OPIK_API_KEY", raising=False)
    monkeypatch.setenv("OPIK_WORKSPACE", "default")
    headers = tracing.opik_headers()
    assert headers == {"Comet-Workspace": "default", "projectName": "beeai-py-expense-approval"}
    monkeypatch.setenv("OPIK_API_KEY", "abc")
    assert tracing.opik_headers()["Authorization"] == "abc"


def _finished_spans():
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

    memory = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(memory))
    tracer = provider.get_tracer("test")
    with tracer.start_as_current_span("OpenAIChatModel", attributes={"openinference.span.kind": "LLM", "llm.provider": "openai"}):
        pass
    with tracer.start_as_current_span("new_token", attributes={"openinference.span.kind": "LLM"}):
        pass
    with tracer.start_as_current_span("policy_lookup"):
        pass
    return memory.get_finished_spans()


def test_cleaner_drops_chunk_spans_and_tags_llm_spans_with_provider():
    from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult

    sent = []

    class Capture(SpanExporter):
        def export(self, spans):
            sent.extend(spans)
            return SpanExportResult.SUCCESS

    tracing.OpikSpanCleaner(Capture()).export(_finished_spans())
    assert [s.name for s in sent] == ["OpenAIChatModel", "policy_lookup"]
    assert sent[0].attributes["gen_ai.system"] == "openai"
    assert "gen_ai.system" not in sent[1].attributes
