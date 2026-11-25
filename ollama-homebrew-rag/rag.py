"""The homebrew handbook RAG pipeline: local embeddings, local LLM, in-memory index."""

import os
import pathlib

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
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


def build_chain(retriever, llm=None):
    """retriever | prompt | llm, one question string in, one answer string out."""
    llm = llm or ChatOllama(
        model=CHAT_MODEL, base_url=OLLAMA_URL, temperature=0, num_predict=200
    )
    prompt = ChatPromptTemplate.from_messages(
        [("system", SYSTEM_PROMPT), ("human", "{question}")]
    )
    return (
        {"context": retriever | format_context, "question": lambda q: q}
        | prompt
        | llm
        | StrOutputParser()
    ).with_config({"run_name": "ask_the_handbook"})
