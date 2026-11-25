"""Question answering over small PDF trail guides, traced and tested with Opik.

Four generated PDFs (one per fictional trail) are split into one chunk per
section, embedded with OpenAI, and queried with gpt-4o-mini. Opik's LlamaIndex
callback records each query as a trace; an Opik test suite then checks, per
section, that the right chunk was retrieved and the right fact was stated.
"""

import os
import pathlib
import re

# Opik reads the project name from this variable when the first trace is
# created; without it traces would land in the "Default Project".
PROJECT_NAME = "llamaindex-trail-guide-qa"
os.environ["OPIK_PROJECT_NAME"] = PROJECT_NAME

import dotenv

# Secrets live in the repo-root .env (OPENAI_API_KEY and friends).
dotenv.load_dotenv(pathlib.Path(__file__).parents[1] / ".env")

import opik
from llama_index.core import Settings, SimpleDirectoryReader, VectorStoreIndex, set_global_handler
from llama_index.core.schema import TextNode
from llama_index.llms.openai import OpenAI

import suite
import trails

# One line turns on Opik's LlamaIndex callback: every query becomes a trace with
# retrieve (embedding) and synthesize (templating, llm) spans underneath it.
set_global_handler("opik")

Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0.0)

DOCS_DIR = trails.DOCS_DIR

SYSTEM_HINT = (
    "You answer questions about hiking trails using only the retrieved guide "
    "excerpts. Quote distances, elevations, fees and quotas exactly. Name the "
    "trail you are answering about. If the excerpts do not cover the question, say so."
)

DEMO_QUESTIONS = [
    "How much elevation do I gain on Heron Ridge Loop?",
    "Do I need a permit for Kestrel Pass Traverse, and what does it cost?",
    "Where can I get drinking water on Marrow Falls Trail?",
    "What should I watch out for at the Old Quarry Trail?",
]

# Headings are exactly the section names, each on its own line.
_HEADING = re.compile(r"^(%s)\s*$" % "|".join(trails.SECTIONS), re.MULTILINE)


def split_sections(trail: str, text: str) -> list[TextNode]:
    """Cut a guide's text into one node per section, tagged with trail and section."""
    parts = _HEADING.split(text)
    # parts = [preamble, heading1, body1, heading2, body2, ...]
    nodes = []
    for heading, body in zip(parts[1::2], parts[2::2]):
        body = " ".join(body.split())
        nodes.append(
            TextNode(
                text=f"{trail} - {heading}: {body}",
                metadata={"trail": trail, "section": heading},
            )
        )
    return nodes


def build_query_engine(top_k: int = 3):
    """Index the trail PDFs, one node per section, and return a query engine."""
    if not sorted(DOCS_DIR.glob("*.pdf")):
        print("No PDFs found - generating the trail guides first.")
        trails.generate_all()
    nodes = []
    for path in sorted(DOCS_DIR.glob("*.pdf")):
        pages = SimpleDirectoryReader(input_files=[str(path)]).load_data()
        text = "\n".join(page.text for page in pages)
        title = text.strip().splitlines()[0].strip()
        nodes.extend(split_sections(title, text))
    index = VectorStoreIndex(nodes)
    return index.as_query_engine(similarity_top_k=top_k)


def retrieved_sections(response) -> list[str]:
    """Trail / section labels of the chunks retrieval returned, best match first."""
    return [
        suite.section_label(n.node.metadata["trail"], n.node.metadata["section"])
        for n in response.source_nodes
    ]


def run_suite(query_engine) -> None:
    # A test suite is an Opik dataset whose items carry plain-language assertions;
    # it shows up under Test suites. Inserting is idempotent for identical items.
    client = opik.Opik()
    test_suite = client.get_or_create_test_suite(
        name=suite.SUITE_NAME,
        project_name=PROJECT_NAME,
        global_assertions=suite.GLOBAL_ASSERTIONS,
    )
    test_suite.insert(suite.suite_rows())

    # The judge only sees what the task returns: section labels (to grade retrieval)
    # and the excerpt text (to grade grounding), next to the answer.
    def task(item: dict) -> dict:
        response = query_engine.query(f"{SYSTEM_HINT}\n\nQuestion: {item['question']}")
        return {
            "input": item,
            "output": {
                "answer": str(response),
                "retrieved_sections": retrieved_sections(response),
                "retrieved_excerpts": [n.node.text for n in response.source_nodes],
            },
        }

    # run_tests runs every item through the task, has an LLM judge score each
    # assertion, and records an experiment you can open from the printed link.
    result = opik.run_tests(
        test_suite=test_suite, task=task, worker_threads=3, generate_report=False
    )

    print(f"\nPass rate: {result.pass_rate:.0%} "
          f"({result.items_passed}/{result.items_total} items passed)")
    hits = 0
    for item_result in result.item_results.values():
        run = item_result.test_results[0]
        data = run.test_case.task_output
        hit = data["input"]["expected_section"] in data["output"]["retrieved_sections"]
        hits += hit
        print(f"  [{'PASS' if item_result.passed else 'FAIL'}] "
              f"[retrieval {'hit' if hit else 'MISS'}] {data['input']['question']}")
        if not item_result.passed:
            for r in item_result.test_results:
                for score in r.score_results:
                    if score.scoring_failed or score.value != 1:
                        print(f"         failed: {score.name} - {score.reason}")
    print(f"Retrieval hit rate: {hits}/{result.items_total}")
    if result.experiment_url:
        print(f"\nView the run: {result.experiment_url}")


def main() -> None:
    query_engine = build_query_engine()
    for question in DEMO_QUESTIONS:
        response = query_engine.query(f"{SYSTEM_HINT}\n\nQuestion: {question}")
        print(f"Q: {question}")
        print(f"A: {response}\n")

    run_suite(query_engine)

    # Traces are sent from a background thread; flush so none are lost on exit.
    opik.flush_tracker()


if __name__ == "__main__":
    main()
