"""The Pydantic AI agent that extracts a TastingNote."""

from functools import cache
from typing import Any

from pydantic_ai import Agent

from tasting.config import MODEL
from tasting.schema import TastingNote

SYSTEM_PROMPT = (
    "You turn a sommelier's scribbled tasting note into a structured record. "
    "Copy only what the note says. If a field is not stated, or the note is "
    "unsure about it, leave it null. Never infer a grape from the region, never "
    "convert a score to another scale, never guess a price or a producer."
)



@cache
def get_agent() -> Agent[None, TastingNote]:
    # Built lazily so importing the module (and unit tests) needs no API key.
    return Agent(MODEL, output_type=TastingNote, system_prompt=SYSTEM_PROMPT)


def extract_note(text: str) -> dict[str, Any]:
    """One extraction: messy note in, typed record (as a dict) out."""
    return get_agent().run_sync(text).output.model_dump()
