"""Opik tracing for both processes: Temporal's OpenTelemetry interceptor + an OTLP exporter."""

import os
from contextlib import contextmanager

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from temporalio.contrib.opentelemetry import TracingInterceptor

from .config import MODEL

OPIK_PROJECT = os.environ.get("OPIK_PROJECT_NAME", "temporal-py-grant-review")


def _otlp_url() -> str:
    # Opik's OTLP ingestion lives under the API base: <api>/v1/private/otel/v1/traces.
    explicit = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    if explicit:
        base = explicit
    else:
        api = os.environ.get("OPIK_URL_OVERRIDE", "http://localhost:5173/api/")
        base = api.rstrip("/") + "/v1/private/otel"
    return base.rstrip("/") + "/v1/traces"


def setup_tracing(service_name: str) -> TracerProvider:
    """Call once per process (client and worker both call it).

    Both processes export to the same Opik project; the project header is what
    routes spans there. Without it the spans land in "Default Project" and the
    client half and the worker half of a trace end up in different places.
    """
    headers = {"projectName": OPIK_PROJECT, "Comet-Workspace": os.environ.get("OPIK_WORKSPACE", "default")}
    if os.environ.get("OPIK_API_KEY"):
        headers["Authorization"] = os.environ["OPIK_API_KEY"]
    provider = TracerProvider(resource=Resource.create({SERVICE_NAME: service_name}))
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=_otlp_url(), headers=headers)))
    trace.set_tracer_provider(provider)
    return provider


def tracing_interceptor() -> TracingInterceptor:
    # Goes on the Temporal client in both processes. It injects the trace context into
    # Temporal's headers on start, and opens StartWorkflow / RunWorkflow / StartActivity /
    # RunActivity spans on the way through, one RunActivity per retry attempt, so the
    # worker's spans join the client's trace and a failed attempt keeps its error.
    return TracingInterceptor()


@contextmanager
def llm_span(name: str, system: str, user: str):
    """Wrap one chat completion in an Opik-readable LLM span.

    Opik maps gen_ai.* attributes to model, provider and token usage (so it can price
    the call) and input.value / output.value to the span's input and output.
    """
    tracer = trace.get_tracer("grant-review")
    with tracer.start_as_current_span(name) as span:
        span.set_attributes(
            {
                "gen_ai.operation.name": "chat",
                "gen_ai.system": "openai",
                "gen_ai.provider.name": "openai",
                "gen_ai.request.model": MODEL,
                "input.value": f"[system] {system}\n\n[user] {user}",
            }
        )
        yield span


def record_completion(span, response, output: str) -> None:
    span.set_attributes(
        {
            "gen_ai.response.model": response.model,
            "gen_ai.usage.input_tokens": response.usage.prompt_tokens,
            "gen_ai.usage.output_tokens": response.usage.completion_tokens,
            "gen_ai.usage.prompt_tokens": response.usage.prompt_tokens,
            "gen_ai.usage.completion_tokens": response.usage.completion_tokens,
            "output.value": output,
        }
    )
