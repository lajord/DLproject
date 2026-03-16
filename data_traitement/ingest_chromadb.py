import os
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
from typing import List, Dict
from config import PATHS, EMBED_MODEL, COLLECTION_NAME

load_dotenv()


def get_collection(chroma_path: str = None):
    """Return (or create) the ChromaDB collection with the OpenAI embedding function."""
    path = chroma_path or PATHS["chroma_db"]
    ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=os.environ["OPENAI_API_KEY"],
        model_name=EMBED_MODEL,
    )
    client = chromadb.PersistentClient(path=path)
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )
    return collection


def ingest_chunks(chunks: List[Dict], chroma_path: str = None, batch_size: int = 100):
    """
    Embed and store chunks into ChromaDB.
    Skips chunks whose ID is already present (idempotent).
    """
    collection = get_collection(chroma_path)
    existing = set(collection.get(include=[])["ids"])

    new_chunks = [c for c in chunks if f"{c['source']}_{c['chunk_index']}" not in existing]
    if not new_chunks:
        print("Nothing to ingest — all chunks already present.")
        return

    for i in range(0, len(new_chunks), batch_size):
        batch = new_chunks[i: i + batch_size]
        collection.add(
            ids=[f"{c['source']}_{c['chunk_index']}" for c in batch],
            documents=[c["text"] for c in batch],
            metadatas=[{k: v for k, v in c.items() if k != "text"} for c in batch],
        )
        print(f"  Ingested batch {i // batch_size + 1} ({len(batch)} chunks)")

    print(f"Done — {len(new_chunks)} new chunks ingested. Collection size: {collection.count()}")


def query(text: str, n_results: int = 5, chroma_path: str = None) -> List[Dict]:
    """Simple semantic search — returns the top-n most relevant chunks."""
    collection = get_collection(chroma_path)
    results = collection.query(query_texts=[text], n_results=n_results)

    hits = []
    for i, doc in enumerate(results["documents"][0]):
        meta = results["metadatas"][0][i]
        hits.append({
            "text": doc,
            "source": meta.get("source"),
            "chapter": meta.get("chapter"),
            "section": meta.get("section"),
            "score": results["distances"][0][i],
        })
    return hits
