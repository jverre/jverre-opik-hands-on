"""Self-contained demo: dev server, worker subprocess, three reviews, clean shutdown."""

import asyncio
import subprocess
import sys

from temporalio.client import Client
from temporalio.testing import WorkflowEnvironment

from .config import TASK_QUEUE, TEMPORAL_PORT, TEMPORAL_UI_PORT, load_applications
from .workflows import GrantReview


async def run() -> None:
    async with await WorkflowEnvironment.start_local(
        port=TEMPORAL_PORT, ui=True, ui_port=TEMPORAL_UI_PORT
    ) as env:
        address = f"localhost:{TEMPORAL_PORT}"
        worker = subprocess.Popen(
            [sys.executable, "-m", "grant_review.worker"],
            env={**__import__("os").environ, "TEMPORAL_ADDRESS": address},
        )
        try:
            await asyncio.sleep(3)
            client: Client = env.client
            for app in load_applications():
                result = await client.execute_workflow(
                    GrantReview.run, app["id"], id=f"review-{app['id']}", task_queue=TASK_QUEUE
                )
                print(f"\n{app['id']} {app['applicant']}")
                print(f"  eligible: {result['eligibility']['eligible']}  budget ok: {result['budget']['ok']}")
                print(f"  {result['summary']}")
        finally:
            worker.terminate()
            worker.wait(timeout=20)


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
