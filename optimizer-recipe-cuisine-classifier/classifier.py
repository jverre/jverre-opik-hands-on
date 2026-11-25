"""A deliberately loose cuisine classifier: the prompt we will later optimize.

`classify` sends one recipe blurb to gpt-4o-mini and returns the raw answer.
Run this file directly to score the baseline prompt on the training set.
"""

import functools
import os
import pathlib

# Some build machines route OpenAI traffic through a local proxy via base-URL
# env vars; the example should talk to the public API, so drop them.
os.environ.pop("OPENAI_BASE_URL", None)
os.environ.pop("OPENAI_API_BASE", None)

import dotenv
from openai import OpenAI

# Keys live in the repo-root .env (or a .env next to this file).
dotenv.load_dotenv(pathlib.Path(__file__).parents[1] / ".env")
dotenv.load_dotenv()

from data import CUISINES, TRAIN

MODEL = "gpt-4o-mini"

# A first draft like many real ones: it names the five cuisines but never says
# how to answer, so the model replies in sentences ("This dish belongs to
# Levantine cuisine.") and exact-match scoring marks them all wrong.
BASELINE_SYSTEM = (
    "You help a food blog tag recipes. Say which cuisine (Levantine, Oaxacan, "
    "Sichuan, Nordic or West African) the dish belongs to."
)


@functools.cache
def _client() -> OpenAI:
    return OpenAI()


def normalize(answer: str) -> str:
    """Lowercase and strip quotes/punctuation, so "Sichuan." still counts."""
    return answer.strip().lower().strip(".!\"'` *").replace(" ", "-")


def is_correct(answer: str, label: str) -> bool:
    """Exact match on the cuisine label: the answer must be only the label."""
    return normalize(answer) == label


def classify(description: str, system: str = BASELINE_SYSTEM) -> str:
    """Ask the model for the cuisine of one recipe description."""
    response = _client().chat.completions.create(
        model=MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": description},
        ],
    )
    return response.choices[0].message.content or ""


def accuracy(items: list[tuple[str, str]], system: str = BASELINE_SYSTEM) -> float:
    """Fraction of items whose answer is exactly the right cuisine label."""
    hits = sum(is_correct(classify(text, system), label) for text, label in items)
    return hits / len(items)


if __name__ == "__main__":
    print(f"cuisines: {', '.join(CUISINES)}")
    sample_text, sample_label = TRAIN[0]
    print(f"sample answer for a {sample_label} dish: {classify(sample_text)!r}")
    print(f"baseline accuracy on {len(TRAIN)} training dishes: {accuracy(TRAIN):.3f}")
