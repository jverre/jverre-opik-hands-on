"""Ask the Alderbank Museum guide a few questions."""

from pathlib import Path

import dotenv

# Provider keys come from a .env in this folder or at the repo root.
dotenv.load_dotenv(Path(__file__).parent / ".env")
dotenv.load_dotenv(Path(__file__).parents[1] / ".env")

from langchain_openai import ChatOpenAI  # noqa: E402

from guide.corpus import load_chunks  # noqa: E402
from guide.graph import build_graph  # noqa: E402
from guide.retrieval import build_store  # noqa: E402

QUESTIONS = [
    "When does the Orrery Room close, and can I get there without stairs?",
    "Can I borrow a wheelchair, and do I need to book one?",
    "Who made the Marlowe No. 4 chronometer and where is it displayed?",
    "Is there a planetarium show at the museum?",  # not in the guide
]


def main() -> None:
    store = build_store(load_chunks())
    app = build_graph(store, ChatOpenAI(model="gpt-4o-mini", temperature=0))
    for question in QUESTIONS:
        result = app.invoke({"question": question})
        print(f"Q: {question}\nA: {result['answer']}\n")


if __name__ == "__main__":
    main()
