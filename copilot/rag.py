"""RAG layer: ingest reference PRDs and retrieve relevant chunks."""

import os
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

REFERENCE_DIR = Path(__file__).parent.parent / "reference_docs"
CHROMA_DIR = Path(__file__).parent.parent / ".chroma"
COLLECTION_NAME = "prd_references"


def get_collection():
    """Get or create the ChromaDB collection with default embeddings."""
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    ef = embedding_functions.DefaultEmbeddingFunction()
    return client.get_or_create_collection(
        name=COLLECTION_NAME, embedding_function=ef
    )


def chunk_document(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split a document into overlapping chunks by character count.

    Splits on paragraph boundaries when possible to keep sections intact.
    """
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        if len(current_chunk) + len(para) > chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            words = current_chunk.split()
            current_chunk = " ".join(words[-overlap:]) + "\n\n" + para
        else:
            current_chunk += "\n\n" + para if current_chunk else para

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


def ingest_references() -> int:
    """Read all markdown files from reference_docs/ and store in ChromaDB.

    Returns the number of chunks ingested.
    """
    collection = get_collection()

    # Clear existing data for clean re-ingest
    existing = collection.get()
    if existing["ids"]:
        collection.delete(ids=existing["ids"])

    md_files = list(REFERENCE_DIR.glob("*.md"))
    if not md_files:
        raise FileNotFoundError(
            f"No .md files found in {REFERENCE_DIR}. Add your reference PRDs there."
        )

    all_chunks = []
    all_ids = []
    all_metadata = []

    for file_path in md_files:
        text = file_path.read_text(encoding="utf-8")
        chunks = chunk_document(text)

        for i, chunk in enumerate(chunks):
            chunk_id = f"{file_path.stem}_chunk_{i}"
            all_chunks.append(chunk)
            all_ids.append(chunk_id)
            all_metadata.append({"source": file_path.name, "chunk_index": i})

    collection.add(documents=all_chunks, ids=all_ids, metadatas=all_metadata)
    return len(all_chunks)


def retrieve(query: str, n_results: int = 3) -> str:
    """Retrieve the most relevant chunks for a given query.

    Returns chunks joined as a single string for prompt injection.
    """
    collection = get_collection()

    if collection.count() == 0:
        return ""

    results = collection.query(query_texts=[query], n_results=n_results)

    chunks = results["documents"][0] if results["documents"] else []
    return "\n\n---\n\n".join(chunks)
