"""Shared settings and data loading for the client, the worker and the activities."""

import json
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

# find_dotenv-style: load a local .env first, then walk up to a repo-root .env.
for parent in [ROOT, *ROOT.parents]:
    if (parent / ".env").is_file():
        load_dotenv(parent / ".env", override=False)

TASK_QUEUE = "grant-review"
MODEL = "gpt-4o-mini"
MAX_AWARD = 5000
TEMPORAL_PORT = int(os.environ.get("TEMPORAL_PORT", "4200"))
TEMPORAL_UI_PORT = int(os.environ.get("TEMPORAL_UI_PORT", "4201"))
TEMPORAL_ADDRESS = os.environ.get("TEMPORAL_ADDRESS", f"localhost:{TEMPORAL_PORT}")


def load_applications() -> list[dict]:
    return json.loads((DATA / "applications.json").read_text())


def get_application(app_id: str) -> dict:
    for app in load_applications():
        if app["id"] == app_id:
            return app
    raise KeyError(f"unknown application {app_id!r}")


def load_rules() -> str:
    return (DATA / "grant_rules.md").read_text()
