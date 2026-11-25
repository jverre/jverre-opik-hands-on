"""The homebrew handbook RAG pipeline: local embeddings, local LLM, in-memory index."""

import operator
import os
import pathlib

import opik
from opik import opik_context
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_ollama import ChatOllama, OllamaEmbeddings

HERE = pathlib.Path(__file__).parent
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
CHAT_MODEL = "llama3.2:1b"
EMBED_MODEL = "nomic-embed-text"
TOP_K = 4

SYSTEM_PROMPT = (
    "You are the Copperkettle brewing assistant. Answer the question using only "
    "the handbook excerpts below. If the excerpts do not cover it, say so. "
    "Answer in at most three sentences.\n\n{context}"
)


def load_chunks(data_dir: pathlib.Path = HERE / "data") -> list[Document]:
    """Split each handbook file into one chunk per '##' section."""
    chunks = []
    for path in sorted(data_dir.glob("*.md")):
        title, *sections = path.read_text().split("\n## ")
        for section in sections:
            heading, _, body = section.partition("\n")
            chunks.append(
                Document(
                    page_content=f"{title.strip()}\n\n## {heading.strip()}\n{body.strip()}",
                    metadata={"source": path.name, "section": heading.strip()},
                )
            )
    return chunks


def format_context(docs: list[Document]) -> str:
    """Join retrieved chunks into the context block of the prompt."""
    return "\n\n---\n\n".join(doc.page_content for doc in docs)


def build_retriever():
    """Embed the handbook with Ollama and return a top-K retriever."""
    store = InMemoryVectorStore.from_documents(
        load_chunks(), OllamaEmbeddings(model=EMBED_MODEL, base_url=OLLAMA_URL)
    )
    return store.as_retriever(search_kwargs={"k": TOP_K})


def make_search(retriever):
    """Wrap the retriever in a function that Opik records as its own span.

    OpikTracer drops the retriever run when the retriever sits directly in the
    chain, so the trace shows nothing between the question and the prompt.
    A named @track function does not get dropped.
    """

    # type="tool" makes this a tool span named search_handbook, nested under
    # the chain's trace; its input is the question and its output is the
    # retrieved sections. Without it, you cannot tell a retrieval miss from a
    # model that ignored good context.
    @opik.track(name="search_handbook", type="tool")
    def search_handbook(question: str) -> dict:
        docs = retriever.invoke(question)
        sections = [f"{d.metadata['source']} / {d.metadata['section']}" for d in docs]
        # Span metadata is searchable in the UI: k and the section list sit
        # next to the span instead of buried in the output text.
        opik_context.update_current_span(metadata={"k": TOP_K, "sections": sections})
        return {"sections": sections, "context": format_context(docs)}

    return search_handbook


def build_chain(retriever, llm=None):
    """question -> search_handbook -> prompt -> llm, one answer string out."""
    llm = llm or ChatOllama(
        model=CHAT_MODEL, base_url=OLLAMA_URL, temperature=0, num_predict=200
    )
    prompt = ChatPromptTemplate.from_messages(
        [("system", SYSTEM_PROMPT), ("human", "{question}")]
    )
    # LangChain records every runnable as a span, so these names are what the
    # trace tree shows around the tool span.
    search = RunnableLambda(make_search(retriever), name="retrieve") | RunnableLambda(
        operator.itemgetter("context"), name="pick_context"
    )
    return (
        {"context": search, "question": RunnableLambda(lambda q: q, name="pass_question")}
        | prompt
        | llm
        | StrOutputParser()
    ).with_config({"run_name": "ask_the_handbook"})
