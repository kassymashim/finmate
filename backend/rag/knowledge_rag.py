"""
RAG Pipeline for FinMate financial knowledge base.

Chunking Strategy: RecursiveCharacterTextSplitter with markdown-aware splitting.
Embedding Model: OpenAI text-embedding-3-small (cost-effective, 1536 dims).
Vector DB: ChromaDB (local, persistent, zero-config).
Retrieval: MMR (Maximal Marginal Relevance) for diversity in results.
"""

import os
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_core.documents import Document
from backend.utils.config import OPENAI_API_KEY, EMBEDDING_MODEL, CHROMA_PERSIST_DIR, KNOWLEDGE_BASE_DIR


def get_text_splitter() -> RecursiveCharacterTextSplitter:
    """
    Markdown-aware chunking: splits on headers first, then paragraphs.
    Chunk size 800 with 200 overlap balances context vs. precision
    for financial advice content.
    """
    return RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=200,
        separators=["\n## ", "\n### ", "\n\n", "\n", ". ", " "],
        keep_separator=True,
    )


def get_embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        openai_api_key=OPENAI_API_KEY,
    )


def build_knowledge_base() -> Chroma:
    """Load documents, chunk them, and create/persist vector store."""
    loader = DirectoryLoader(
        KNOWLEDGE_BASE_DIR,
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )
    documents = loader.load()

    splitter = get_text_splitter()
    chunks = splitter.split_documents(documents)

    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_id"] = i
        source = os.path.basename(chunk.metadata.get("source", ""))
        chunk.metadata["topic"] = source.replace(".md", "").replace("_", " ").title()

    embeddings = get_embeddings()
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_PERSIST_DIR,
        collection_name="finmate_knowledge",
    )

    print(f"Built knowledge base with {len(chunks)} chunks from {len(documents)} documents")
    return vectorstore


def get_vectorstore() -> Chroma:
    """Load existing vector store or build if not present."""
    embeddings = get_embeddings()

    if os.path.exists(CHROMA_PERSIST_DIR):
        return Chroma(
            persist_directory=CHROMA_PERSIST_DIR,
            embedding_function=embeddings,
            collection_name="finmate_knowledge",
        )

    return build_knowledge_base()


def retrieve_context(query: str, k: int = 4) -> list[Document]:
    """
    Retrieve relevant financial knowledge using MMR for diversity.
    MMR prevents returning near-duplicate chunks while maintaining relevance.
    """
    vectorstore = get_vectorstore()
    results = vectorstore.max_marginal_relevance_search(
        query,
        k=k,
        fetch_k=10,
        lambda_mult=0.7,  # 0.7 balances relevance (1.0) vs diversity (0.0)
    )
    return results


def format_context(documents: list[Document]) -> str:
    """Format retrieved documents into context string for LLM."""
    context_parts = []
    for doc in documents:
        topic = doc.metadata.get("topic", "General")
        context_parts.append(f"[Source: {topic}]\n{doc.page_content}")
    return "\n\n---\n\n".join(context_parts)


if __name__ == "__main__":
    print("Building knowledge base...")
    build_knowledge_base()
    print("\nTesting retrieval...")
    results = retrieve_context("How should I budget my money?")
    for r in results:
        print(f"\n[{r.metadata.get('topic')}] {r.page_content[:100]}...")
