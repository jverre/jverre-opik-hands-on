"""Self-contained demo: dev server, worker subprocess, three reviews, clean shutdown."""

import asyncio
import json
import os
import subprocess
import sys

from opentelemetry import trace
from temporalio.client import Client
from temporalio.testing import WorkflowEnvironment

from .config import TASK_QUEUE, TEMPORAL_PORT, TEMPORAL_UI_PORT, load_applications
from .tracing import setup_tracing, tracing_interceptor
from .workflows import GrantReview


async def run() -> None:
    provider = setup_tracing("grant-client")  # client-side exporter: the root span and StartWorkflow
    async with await WorkflowEnvironment.start_local(
        port=TEMPORAL_PORT, ui=True, ui_port=TEMPORAL_UI_PORT
    ) as env:
        address = f"localhost:{TEMPORAL_PORT}"
        worker = subprocess.Popen(
            [sys.executable, "-m", "grant_review.worker"],
            env={**os.environ, "TEMPORAL_ADDRESS": address},
        )
        try:
            await asyncio.sleep(3)
            client = await Client.connect(address, interceptors=[tracing_interceptor()])
            tracer = trace.get_tracer("grant-client")
            for app in load_applications():
                # Root span of the Opik trace. The interceptor starts the workflow inside it,
                # so everything the worker does hangs under this one trace.
                with tracer.start_as_current_span(f"review:{app['id']}") as span:
                    span.set_attribute("input.value", json.dumps(app))
                    result = await client.execute_workflow(
                        GrantReview.run, app["id"], id=f"review-{app['id']}", task_queue=TASK_QUEUE
                    )
                    span.set_attribute("output.value", json.dumps(result))
                print(f"\n{app['id']} {app['applicant']}")
                print(f"  eligible: {result['eligibility']['eligible']}  budget ok: {result['budget']['ok']}")
                print(f"  {result['summary']}")
        finally:
            worker.terminate()
            worker.wait(timeout=20)  # SIGTERM lets the worker flush its spans
            provider.shutdown()  # flush the client's spans to Opik


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
