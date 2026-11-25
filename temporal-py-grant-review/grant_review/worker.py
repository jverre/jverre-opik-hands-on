"""The worker process: runs the workflow and the activities."""

import asyncio

from temporalio.client import Client
from temporalio.worker import Worker

from .activities import check_budget, check_eligibility, write_reviewer_summary
from .config import TASK_QUEUE, TEMPORAL_ADDRESS
from .workflows import GrantReview


async def main() -> None:
    client = await Client.connect(TEMPORAL_ADDRESS)
    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[GrantReview],
        activities=[check_eligibility, check_budget, write_reviewer_summary],
    )
    print(f"WORKER_READY on {TEMPORAL_ADDRESS}, task queue {TASK_QUEUE!r}", flush=True)
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
