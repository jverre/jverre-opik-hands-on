"""Loads the fictional Harbor & Pine Outfitters expense data from data/*.json."""
import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _load(name: str):
    return json.loads((DATA_DIR / name).read_text())


def load_policy() -> dict:
    return _load("policy.json")


def load_employees() -> dict:
    return _load("employees.json")


def load_receipts() -> dict:
    return _load("receipts.json")


def load_reports() -> list[dict]:
    return _load("reports.json")
