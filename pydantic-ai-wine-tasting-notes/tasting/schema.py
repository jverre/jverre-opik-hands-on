"""The typed record the agent must fill in."""

from pydantic import BaseModel, Field


class TastingNote(BaseModel):
    """One wine, as described in a free-text tasting note."""

    wine: str | None = Field(None, description="Wine name or appellation as written")
    producer: str | None = Field(None, description="Estate, domaine or winery, only if named")
    vintage: int | None = Field(None, description="Four-digit year; null for NV or if unclear")
    region: str | None = Field(None, description="Region or appellation the note states")
    grape: str | None = Field(None, description="Grape variety, only if the note says so")
    score_100: int | None = Field(
        None, description="Score out of 100, only if the note gives one on that scale"
    )
    price: float | None = Field(None, description="Price as a number, only if one is stated")
    currency: str | None = Field(None, description="ISO currency code for the price")
    descriptors: list[str] = Field(
        default_factory=list, description="Aroma, flavour and structure words from the note"
    )
