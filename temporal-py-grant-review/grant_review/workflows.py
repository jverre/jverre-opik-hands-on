"""The durable review workflow."""

from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from .activities import check_budget, check_eligibility, write_reviewer_summary

RETRY = RetryPolicy(initial_interval=timedelta(seconds=1), maximum_attempts=3)
TIMEOUT = timedelta(seconds=60)


@workflow.defn
class GrantReview:
    @workflow.run
    async def run(self, app_id: str) -> dict:
        eligibility = await workflow.execute_activity(
            check_eligibility, app_id, start_to_close_timeout=TIMEOUT, retry_policy=RETRY
        )
        budget = await workflow.execute_activity(
            check_budget, app_id, start_to_close_timeout=TIMEOUT, retry_policy=RETRY
        )
        summary = await workflow.execute_activity(
            write_reviewer_summary,
            args=[app_id, eligibility, budget],
            start_to_close_timeout=TIMEOUT,
            retry_policy=RETRY,
        )
        return {"app_id": app_id, "eligibility": eligibility, "budget": budget, "summary": summary}
