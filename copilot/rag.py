"""RAG layer: ingest reference PRDs and tickets, retrieve relevant chunks."""

from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

PROJECT_ROOT = Path(__file__).parent.parent
REFERENCE_DIRS = {
    "prd": PROJECT_ROOT / "reference_docs",
    "ticket": PROJECT_ROOT / "reference_tickets",
}
CHROMA_DIR = PROJECT_ROOT / ".chroma"
COLLECTION_NAME = "pm_references"


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


def _ingest_directory(collection, ref_dir: Path, doc_type: str) -> int:
    """Ingest all .md files from a directory with doc_type metadata."""
    if not ref_dir.exists():
        return 0

    md_files = list(ref_dir.glob("*.md"))
    if not md_files:
        return 0

    all_chunks = []
    all_ids = []
    all_metadata = []

    for file_path in md_files:
        text = file_path.read_text(encoding="utf-8")
        chunks = chunk_document(text)

        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc_type}_{file_path.stem}_chunk_{i}"
            all_chunks.append(chunk)
            all_ids.append(chunk_id)
            all_metadata.append({
                "source": file_path.name,
                "chunk_index": i,
                "doc_type": doc_type,
            })

    if all_chunks:
        collection.add(documents=all_chunks, ids=all_ids, metadatas=all_metadata)

    return len(all_chunks)


def ingest_references() -> dict[str, int]:
    """Ingest markdown files from reference_docs/ and reference_tickets/.

    Returns a dict with chunk counts per doc_type, e.g. {"prd": 12, "ticket": 5}.
    """
    collection = get_collection()

    existing = collection.get()
    if existing["ids"]:
        collection.delete(ids=existing["ids"])

    counts = {}
    total = 0
    for doc_type, ref_dir in REFERENCE_DIRS.items():
        count = _ingest_directory(collection, ref_dir, doc_type)
        counts[doc_type] = count
        total += count

    if total == 0:
        raise FileNotFoundError(
            "No .md files found in reference_docs/ or reference_tickets/. "
            "Add your reference PRDs and/or tickets there."
        )

    return counts


def retrieve(query: str, n_results: int = 3, doc_type: str | None = None) -> str:
    """Retrieve the most relevant chunks for a given query.

    Args:
        query: Search query text.
        n_results: Number of chunks to return.
        doc_type: Optional filter -- "prd" or "ticket". None returns all types.

    Returns chunks joined as a single string for prompt injection.
    """
    collection = get_collection()

    if collection.count() == 0:
        return ""

    where_filter = {"doc_type": doc_type} if doc_type else None
    results = collection.query(
        query_texts=[query], n_results=n_results, where=where_filter
    )

    chunks = results["documents"][0] if results["documents"] else []
    return "\n\n---\n\n".join(chunks)
