"""Send Pydantic AI's OpenTelemetry spans to Opik."""

import os

from tasting.config import PROJECT_NAME

_DEFAULT_URL = "http://localhost:5173/api/"  # a local, self-hosted Opik


def _otlp_endpoint() -> str:
    # Opik serves OTLP/HTTP under <api base>/v1/private/otel.
    base = os.getenv("OPIK_URL_OVERRIDE", _DEFAULT_URL).rstrip("/")
    return f"{base}/v1/private/otel"


def setup_tracing() -> None:
    """Configure logfire so every Pydantic AI run becomes an Opik trace.

    Pydantic AI has no Opik callback: it emits OpenTelemetry spans (via
    logfire), and Opik ingests them over OTLP. Call this once at startup.
    """
    # The OTLP exporter reads these env vars: the workspace header routes the
    # spans, and projectName decides which Opik project they land in.
    headers = [
        f"Comet-Workspace={os.getenv('OPIK_WORKSPACE', 'default')}",
        f"projectName={PROJECT_NAME}",
    ]
    if api_key := os.getenv("OPIK_API_KEY"):  # only needed for Comet cloud
        headers.insert(0, f"Authorization={api_key}")
    os.environ.setdefault("OTEL_EXPORTER_OTLP_ENDPOINT", _otlp_endpoint())
    os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = ",".join(headers)
    os.environ["OTEL_METRICS_EXPORTER"] = "none"
    os.environ["OPIK_PROJECT_NAME"] = PROJECT_NAME

    import logfire
    from opik.integrations.otel import OpikSpanProcessor

    # OpikSpanProcessor stitches the agent's OTel spans under the surrounding
    # @opik.track span; without it each model call becomes its own orphan trace.
    logfire.configure(
        send_to_logfire=False,
        service_name=PROJECT_NAME,
        additional_span_processors=[OpikSpanProcessor()],
    )
    # Turns on the Pydantic AI spans: invoke_agent, chat <model>, tool calls.
    logfire.instrument_pydantic_ai()


def flush_tracing() -> None:
    """Push buffered spans out before the process exits."""
    import logfire
    import opik

    logfire.force_flush()  # OTLP batch exporter -> Opik
    opik.flush_tracker()  # spans created by @opik.track
