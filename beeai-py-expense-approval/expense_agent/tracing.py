"""Wires BeeAI to Opik. This is the only file that knows tracing exists.

BeeAI emits OpenInference spans; a plain OTLP/HTTP exporter ships them to Opik's
OpenTelemetry endpoint. Auth and routing (workspace + project) travel as HTTP headers.
"""
import copy
import os

from openinference.instrumentation.beeai import BeeAIInstrumentor
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SpanExporter, SpanExportResult

PROJECT_NAME = "beeai-py-expense-approval"


def opik_otlp_traces_url() -> str:
    """Opik's OTLP traces URL: an explicit OTel endpoint wins, else derive it from the Opik API URL."""
    base = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not base:
        api = os.environ.get("OPIK_URL_OVERRIDE", "http://localhost:5173/api/")
        base = api.rstrip("/") + "/v1/private/otel"
    return base.rstrip("/") + "/v1/traces"


def opik_headers() -> dict[str, str]:
    headers = {
        # Comet-Workspace picks the workspace; projectName routes every trace into this one Opik project.
        "Comet-Workspace": os.environ.get("OPIK_WORKSPACE", "default"),
        "projectName": PROJECT_NAME,
    }
    if os.environ.get("OPIK_API_KEY"):  # only Opik Cloud needs a key; local Opik takes none
        headers["Authorization"] = os.environ["OPIK_API_KEY"]
    return headers


def with_provider(span):
    """Copy `llm.provider` into the `gen_ai.system` attribute on llm spans.

    BeeAI already records llm.provider ("openai") and the model name, but Opik reads the provider from
    `gen_ai.system`. Without it the llm span has token usage but no provider, so no dollar cost is estimated.
    """
    provider = span.attributes.get("llm.provider")
    if span.attributes.get("openinference.span.kind") != "LLM" or not provider:
        return span
    tagged = copy.copy(span)
    tagged._attributes = {**span.attributes, "gen_ai.system": provider}
    return tagged


class OpikSpanCleaner(SpanExporter):
    """Forwards spans to the real exporter, minus the per-chunk `new_token` spans.

    BeeAI streams every model call, and the instrumentation turns each streamed chunk into its own
    span: about 190 `new_token` spans per trace next to ~10 meaningful ones. Dropping them keeps the
    Opik trace tree readable and the span counts honest; the llm span still carries the full output.
    """

    def __init__(self, inner: SpanExporter) -> None:
        self._inner = inner

    def export(self, spans) -> SpanExportResult:
        return self._inner.export([with_provider(s) for s in spans if s.name != "new_token"])

    def shutdown(self) -> None:
        self._inner.shutdown()

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return self._inner.force_flush(timeout_millis)


def setup_tracing() -> TracerProvider:
    provider = TracerProvider()
    # BatchSpanProcessor buffers spans and posts them to Opik in the background.
    provider.add_span_processor(
        BatchSpanProcessor(
            OpikSpanCleaner(OTLPSpanExporter(endpoint=opik_otlp_traces_url(), headers=opik_headers()))
        )
    )
    trace.set_tracer_provider(provider)
    # BeeAIInstrumentor hooks the framework: each agent run becomes one trace with a root ReAct span
    # (iterations summarised in its metadata), one llm span per model call and one span per tool call.
    BeeAIInstrumentor().instrument()
    return provider


def flush_tracing(provider: TracerProvider) -> None:
    # Without this the last batch of spans can be lost when the process exits.
    provider.force_flush()
    provider.shutdown()
