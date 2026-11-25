"""Ask the Copperkettle homebrewing handbook four questions, fully offline."""

import os
import pathlib

import dotenv

# Optional: pick up OPIK_* and OLLAMA_URL from the repo-root .env.
dotenv.load_dotenv(pathlib.Path(__file__).parents[1] / ".env")

# Every trace must land in this Opik project (set before the SDK is imported).
PROJECT_NAME = "ollama-homebrew-rag"
os.environ["OPIK_PROJECT_NAME"] = PROJECT_NAME

import opik  # noqa: E402
from opik.integrations.langchain import OpikTracer  # noqa: E402

import rag  # noqa: E402

QUESTIONS = [
    "What temperature should I mash at for a dry, crisp saison?",
    "How should I add hops for a hazy IPA whirlpool?",
    "My fermentation is stuck at 1.030. What should I do first?",
    "How long does the sanitizer need to touch a surface?",
]


def main() -> None:
    chain = rag.build_chain(rag.build_retriever())
    # OpikTracer is a LangChain callback: each chain.invoke becomes one trace
    # (named ask_the_handbook) with a child span per runnable and the local
    # model name on the ChatOllama span. No cloud LLM is involved; only the
    # trace goes to Opik.
    tracer = OpikTracer(project_name=PROJECT_NAME, tags=["ollama", "local"])
    for question in QUESTIONS:
        answer = chain.invoke(question, config={"callbacks": [tracer]})
        print(f"Q: {question}\nA: {answer}\n")
    # Traces are sent from a background thread; flush so none are lost at exit.
    opik.flush_tracker()


if __name__ == "__main__":
    main()
