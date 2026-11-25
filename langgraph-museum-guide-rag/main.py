"""Ask the Alderbank Museum guide a few questions."""

import os
from pathlib import Path

import dotenv

PROJECT_NAME = "langgraph-museum-guide-rag"
# Set before opik is imported so the @opik.track spans and the tracer land in
# the same project; otherwise they would split between this one and "Default Project".
os.environ["OPIK_PROJECT_NAME"] = PROJECT_NAME

# Provider keys come from a .env in this folder or at the repo root.
dotenv.load_dotenv(Path(__file__).parent / ".env")
dotenv.load_dotenv(Path(__file__).parents[1] / ".env")

import opik  # noqa: E402
from langchain_openai import ChatOpenAI  # noqa: E402
from opik.integrations.langchain import OpikTracer  # noqa: E402

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
    # One tracer for the run; it logs into PROJECT_NAME.
    tracer = OpikTracer(project_name=PROJECT_NAME)
    app = build_graph(store, ChatOpenAI(model="gpt-4o-mini", temperature=0), tracer=tracer)
    for question in QUESTIONS:
        result = app.invoke({"question": question})
        print(f"Q: {question}\nA: {result['answer']}\n")

    # Traces are sent from a background thread; flush so none are lost at exit.
    opik.flush_tracker()


if __name__ == "__main__":
    main()
