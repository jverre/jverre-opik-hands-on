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
from checks import CASES, answer_has_fact  # noqa: E402


def main() -> None:
    chain = rag.build_chain(rag.build_retriever())
    client = opik.Opik(project_name=PROJECT_NAME)
    for case in CASES:
        # OpikTracer is a LangChain callback: each chain.invoke becomes one trace
        # (named ask_the_handbook) with a child span per runnable, and an llm
        # span for the local ChatOllama call. No cloud LLM is involved; only
        # the trace goes to Opik.
        tracer = OpikTracer(project_name=PROJECT_NAME, tags=["ollama", "local"])
        answer = chain.invoke(case.question, config={"callbacks": [tracer]})
        score = answer_has_fact(answer, case.expected_fact)

        # A feedback score on the trace shows up as a column in the traces
        # table, so you can sort for the answers that missed the fact.
        trace_id = tracer.created_traces()[0].id
        client.log_traces_feedback_scores(
            [{"id": trace_id, "name": "answer_has_fact", "value": score,
              "reason": f"looked for {case.expected_fact!r}"}],
            project_name=PROJECT_NAME,
        )
        print(f"Q: {case.question}\nA: {answer}\n[answer_has_fact={score}]\n")
    # Traces and scores are sent from a background thread; flush so none are
    # lost when the script exits.
    opik.flush_tracker()


if __name__ == "__main__":
    main()
