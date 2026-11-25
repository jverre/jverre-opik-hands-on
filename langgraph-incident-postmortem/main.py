"""Draft a blameless post-mortem with a LangGraph agent team, traced in Opik.

A planner splits an incident into lines of inquiry, an investigator loops over
them against an offline corpus of fictional alerts, logs and chat excerpts in
data/, and a writer drafts the post-mortem. The compiled graph is wrapped once
so the whole run lands in Opik as a single trace.
"""

import functools
import math
import os
import pathlib
import re

PROJECT_NAME = "langgraph-incident-postmortem"
# Opik's default project for this process; also passed explicitly to OpikTracer below.
os.environ.setdefault("OPIK_PROJECT_NAME", PROJECT_NAME)

import dotenv

# Keys (OPENAI_API_KEY, optional OPIK_*) come from a local .env or the repo-root one.
dotenv.load_dotenv(pathlib.Path(__file__).parent / ".env")
dotenv.load_dotenv(pathlib.Path(__file__).parents[1] / ".env")

import opik
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from opik.integrations.langchain import OpikTracer, track_langgraph
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

DATA_DIR = pathlib.Path(__file__).parent / "data"
MODEL = "gpt-4o-mini"


@functools.cache
def get_llm() -> ChatOpenAI:
    """Built on first use so importing this module needs no API key."""
    return ChatOpenAI(model=MODEL, temperature=0)


# --- The offline corpus: alerts, logs, chat and notes, ranked by keyword overlap ---

def load_corpus(data_dir: pathlib.Path = DATA_DIR) -> list[dict]:
    """One searchable entry per '##' section of each file in data/."""
    entries = []
    for path in sorted(data_dir.glob("*.md")):
        title, *sections = path.read_text().split("\n## ")
        for section in sections:
            entries.append({"source": path.name, "text": f"{title.strip()}\n\n## {section.strip()}"})
    return entries


STOPWORDS = frozenset(
    "the a an and or of to in for is are was were be been what how why when which who "
    "did does do with on by as at it its if into from that this these those not no so "
    "during after before between during incident".split()
)


def rarity(term: str, corpus: list[dict]) -> float:
    """Weight a term by how few sections contain it (a tiny IDF)."""
    containing = sum(1 for e in corpus if term in e["text"].lower())
    return math.log(len(corpus) / containing) if containing else 0.0


# type="tool" makes each lookup a tool span nested under the investigator pass that called it,
# showing exactly which excerpts the model was given. It is a plain function when tracking is off.
@opik.track(name="search_corpus", type="tool")
def search_corpus(query: str, k: int = 3, corpus: list[dict] | None = None) -> list[dict]:
    """Rank corpus sections by the rarity-weighted query terms they contain."""
    corpus = corpus if corpus is not None else CORPUS
    terms = set(re.findall(r"[a-z0-9]+", query.lower())) - STOPWORDS

    def score(entry: dict) -> float:
        text = entry["text"].lower()
        return sum(rarity(t, corpus) for t in terms if t in text)

    return sorted(corpus, key=score, reverse=True)[:k]


CORPUS = load_corpus()


# --- Shared state -------------------------------------------------------------

class Finding(TypedDict):
    inquiry: str
    answer: str
    sources: list[str]


class PostmortemState(TypedDict):
    incident: str
    inquiries: list[str]
    findings: list[Finding]
    draft: str


# --- Agent 1: the planner -----------------------------------------------------

class InvestigationPlan(BaseModel):
    """The planner's output: 3 to 4 focused lines of inquiry."""

    inquiries: list[str] = Field(description="3 to 4 questions that together explain the incident")


def planner(state: PostmortemState) -> dict:
    """Split the incident into lines of inquiry for the investigator."""
    plan = get_llm().with_structured_output(InvestigationPlan).invoke([
        ("system",
         "You lead a blameless post-mortem. The evidence is a fixed set of alerts, service "
         "logs, chat excerpts, release notes and a runbook. Split the incident into 3-4 "
         "concrete questions answerable from that evidence, covering the timeline, the "
         "trigger, how the team responded, and what process gaps allowed it."),
        ("user", state["incident"]),
    ])
    return {"inquiries": plan.inquiries, "findings": []}


# --- Agent 2: the investigator (runs once per inquiry) ------------------------

def investigator(state: PostmortemState) -> dict:
    """Answer the next open inquiry from the best-matching evidence."""
    inquiry = state["inquiries"][len(state["findings"])]
    hits = search_corpus(inquiry)
    evidence = "\n\n---\n\n".join(f"[{h['source']}]\n{h['text']}" for h in hits)
    answer = get_llm().invoke([
        ("system",
         "You are an incident investigator. Answer using only the evidence below. Quote "
         "timestamps and numbers, and name the source file for each claim. If the evidence "
         "does not answer it, say so.\n\n" + evidence),
        ("user", inquiry),
    ])
    finding: Finding = {
        "inquiry": inquiry,
        "answer": answer.content,
        "sources": sorted({h["source"] for h in hits}),
    }
    return {"findings": state["findings"] + [finding]}


def route_investigation(state: PostmortemState) -> str:
    """Loop back to the investigator until every inquiry has a finding."""
    return "investigator" if len(state["findings"]) < len(state["inquiries"]) else "writer"


# --- Agent 3: the writer ------------------------------------------------------

def format_notes(findings: list[Finding]) -> str:
    return "\n\n".join(
        f"### {f['inquiry']}\n{f['answer']}\n(Sources: {', '.join(f['sources'])})" for f in findings
    )


def writer(state: PostmortemState) -> dict:
    """Draft the blameless post-mortem from the findings."""
    draft = get_llm().invoke([
        ("system",
         "You are the writer. Draft a blameless post-mortem in markdown with sections: "
         "Summary, Impact, Timeline, Contributing factors, What went well, Action items. "
         "Describe systems and decisions, never personal fault. Use only the notes below "
         "and keep every time and number accurate. Under 500 words.\n\n" + format_notes(state["findings"])),
        ("user", state["incident"]),
    ])
    return {"draft": draft.content}


# --- Wire the graph: planner -> (investigator loop) -> writer -----------------

def build_graph():
    graph = StateGraph(PostmortemState)
    graph.add_node("planner", planner)
    graph.add_node("investigator", investigator)
    graph.add_node("writer", writer)
    graph.add_edge(START, "planner")
    graph.add_edge("planner", "investigator")
    graph.add_conditional_edges(
        "investigator", route_investigation, {"investigator": "investigator", "writer": "writer"}
    )
    graph.add_edge("writer", END)
    return graph.compile()


INCIDENT = (
    "On 3 March 2026 the Ledgerly invoice API returned errors to customers for about 50 "
    "minutes. Write the blameless post-mortem."
)


def main() -> None:
    # OpikTracer is a LangChain callback; track_langgraph attaches it to the compiled graph
    # together with the graph's structure. Each run becomes ONE trace: a span per node pass
    # (planner, investigator x N, writer) with the ChatOpenAI llm spans nested inside, and the
    # loop is drawn in the trace's agent-graph view.
    tracer = OpikTracer(project_name=PROJECT_NAME)
    app = track_langgraph(build_graph(), tracer)

    print(f"Incident: {INCIDENT}\n")
    result = app.invoke({"incident": INCIDENT})

    print("Lines of inquiry:")
    for i, q in enumerate(result["inquiries"], 1):
        print(f"  {i}. {q}")
    print(f"\n{len(result['findings'])} investigator passes. Draft post-mortem:\n")
    print(result["draft"])

    # Traces are sent from a background thread; flush so a short script doesn't exit before they land.
    tracer.flush()
    opik.flush_tracker()


if __name__ == "__main__":
    main()
