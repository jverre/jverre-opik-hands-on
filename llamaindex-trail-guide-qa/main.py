"""Question answering over small PDF trail guides with LlamaIndex.

Four generated PDFs (one per fictional trail) are split into one chunk per
section, embedded with OpenAI, and queried with gpt-4o-mini.
"""

import pathlib
import re

import dotenv

# Secrets live in the repo-root .env (OPENAI_API_KEY and friends).
dotenv.load_dotenv(pathlib.Path(__file__).parents[1] / ".env")

from llama_index.core import Settings, SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.schema import TextNode
from llama_index.llms.openai import OpenAI

import trails

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


def main() -> None:
    query_engine = build_query_engine()
    for question in DEMO_QUESTIONS:
        response = query_engine.query(f"{SYSTEM_HINT}\n\nQuestion: {question}")
        print(f"Q: {question}")
        print(f"A: {response}\n")


if __name__ == "__main__":
    main()
