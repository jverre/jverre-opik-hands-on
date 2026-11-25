"""Deterministic budget sanity check (no model involved)."""

from .config import MAX_AWARD


def check_budget(app: dict) -> dict:
    total = sum(line["cost"] for line in app["budget"])
    problems = []
    if total != app["requested_amount"]:
        problems.append(f"budget lines add up to {total}, but {app['requested_amount']} was requested")
    if app["requested_amount"] > MAX_AWARD:
        problems.append(f"request exceeds the {MAX_AWARD} maximum award")
    return {"line_total": total, "ok": not problems, "problems": problems}
