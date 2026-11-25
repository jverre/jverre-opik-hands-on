"""The worker process: runs the workflow and the activities."""

import asyncio
import signal

from temporalio.client import Client
from temporalio.worker import Worker

from .activities import check_budget, check_eligibility, write_reviewer_summary
from .config import TASK_QUEUE, TEMPORAL_ADDRESS
from .tracing import setup_tracing, tracing_interceptor
from .workflows import GrantReview


async def main() -> None:
    provider = setup_tracing("grant-worker")  # worker-side exporter: workflow, activity and LLM spans
    client = await Client.connect(TEMPORAL_ADDRESS, interceptors=[tracing_interceptor()])
    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[GrantReview],
        activities=[check_eligibility, check_budget, write_reviewer_summary],
    )
    print(f"WORKER_READY on {TEMPORAL_ADDRESS}, task queue {TASK_QUEUE!r}", flush=True)
    # Turn SIGTERM into a graceful stop so the finally block below runs.
    asyncio.get_running_loop().add_signal_handler(signal.SIGTERM, lambda: asyncio.create_task(worker.shutdown()))
    try:
        await worker.run()
    finally:
        provider.shutdown()  # flush buffered spans to Opik before the process exits


if __name__ == "__main__":
    asyncio.run(main())
