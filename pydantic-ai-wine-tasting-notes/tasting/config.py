"""Environment loading and shared constants."""

from pathlib import Path

from dotenv import load_dotenv

PROJECT_NAME = "pydantic-ai-wine-tasting-notes"
MODEL = "openai:gpt-4o-mini"

ROOT = Path(__file__).resolve().parent.parent
NOTES_FILE = ROOT / "data" / "notes.json"


def load_env() -> None:
    """Load keys from the repository-level .env first, then a local one."""
    load_dotenv(ROOT.parent / ".env")
    load_dotenv(ROOT / ".env")
