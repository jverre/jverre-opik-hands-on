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
from guide.evaluation import run_experiment, summarize  # noqa: E402
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
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    # One tracer for the run; it logs into PROJECT_NAME.
    tracer = OpikTracer(project_name=PROJECT_NAME)

    # 1. Tracing demo: a few questions through the default graph (k=4).
    app = build_graph(store, llm, tracer=tracer)
    for question in QUESTIONS:
        result = app.invoke({"question": question})
        print(f"Q: {question}\nA: {result['answer']}\n")

    # 2. Two experiments over the same dataset: the default k=4 and a starved k=1.
    # Opik lists them side by side so the per-question score changes are visible.
    for k, name in [(4, "k4-baseline"), (1, "k1-starved")]:
        evaluation = run_experiment(build_graph(store, llm, k=k, tracer=tracer), name, k, PROJECT_NAME)
        scores = ", ".join(f"{n}={v:.2f}" for n, v in summarize(evaluation).items())
        print(f"{name}: {scores}\n  {evaluation.experiment_url}")

    # Traces are sent from a background thread; flush so none are lost at exit.
    opik.flush_tracker()


if __name__ == "__main__":
    main()
