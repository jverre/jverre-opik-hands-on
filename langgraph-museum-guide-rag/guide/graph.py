"""The two-node graph: retrieve -> generate."""

from typing import Any

from opik.integrations.langchain import OpikTracer, track_langgraph
from langchain_core.language_models import BaseChatModel
from langchain_core.vectorstores import InMemoryVectorStore
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from guide.retrieval import search

DEFAULT_K = 4

SYSTEM_PROMPT = (
    "You are the visitor-guide assistant for the Alderbank Museum of Tides and "
    "Timekeeping. Answer using only the guide excerpts below. If they do not "
    "contain the answer, say you don't know. Be concise.\n\n{context}"
)


class State(TypedDict, total=False):
    question: str
    context: list[str]
    answer: str


def format_context(chunks: list[str]) -> str:
    return "\n\n---\n\n".join(chunks)


def build_graph(store: InMemoryVectorStore, llm: BaseChatModel, k: int = DEFAULT_K,
                tracer: OpikTracer | None = None) -> Any:
    """Compile the graph. The store, model and k are fixed per compiled graph."""

    def retrieve(state: State) -> dict:
        return {"context": search(store, state["question"], k)}

    def generate(state: State) -> dict:
        system = SYSTEM_PROMPT.format(context=format_context(state["context"]))
        reply = llm.invoke([("system", system), ("user", state["question"])])
        return {"answer": reply.content}

    graph = StateGraph(State)
    graph.add_node("retrieve", retrieve)
    graph.add_node("generate", generate)
    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", END)
    app = graph.compile()
    if tracer is None:
        return app
    # track_langgraph attaches the tracer to the compiled graph once: every
    # app.invoke() becomes one trace, with a span per node and the chat model
    # call nested as an llm span. No callbacks to pass at the call sites.
    return track_langgraph(app, tracer)
