import chromadb
from openai import OpenAI
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'data_traitement'))
from config import COLLECTION_NAME, EMBED_MODEL, PATHS

_client = None
_collection = None
_openai = None


def _get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=PATHS["chroma_db"])
        _collection = _client.get_collection(COLLECTION_NAME)
    return _collection


def _embed(text: str) -> list[float]:
    global _openai
    if _openai is None:
        _openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = _openai.embeddings.create(model=EMBED_MODEL, input=text)
    return response.data[0].embedding


def retrieve(question: str, k: int = 5) -> list[dict]:
    """Query ChromaDB and return top-k chunks with metadata."""
    collection = _get_collection()
    embedding = _embed(question)

    results = collection.query(
        query_embeddings=[embedding],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append({
            "text": doc,
            "source": meta.get("source", "unknown"),
            "chapter": meta.get("chapter", ""),
            "section": meta.get("section", ""),
            "chunk_index": meta.get("chunk_index", -1),
            "score": round(1 - dist, 4),
        })

    return chunks
