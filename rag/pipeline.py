import logging
from retriever import retrieve
from reranker import rerank
from prompt import build_prompt
from llm import call_llm

logger = logging.getLogger("rag.pipeline")

RETRIEVE_K = 20
RERANK_TOP_K = 5


def ask(question: str, verbose: bool = False) -> dict:
    """
    Full RAG pipeline with reranking.
    Returns: {answer: str, sources: list[dict]}
    """
    logger.info(f"Question: {question!r}")

    chunks = retrieve(question, k=RETRIEVE_K)
    logger.info(f"[retrieve] {len(chunks)} chunks retrieved")

    chunks = rerank(question, chunks, top_k=RERANK_TOP_K)
    logger.info(f"[rerank]   {len(chunks)} chunks kept")
    for i, c in enumerate(chunks, 1):
        label = c["source"]
        if c.get("section"):
            label += f" > {c['section']}"
        logger.info(f"  [{i}] rerank={c['rerank_score']:.3f} | embed={c['score']:.3f} | {label}")
        logger.info(f"       {c['text'][:120].strip()}...")

    messages = build_prompt(question, chunks)
    answer = call_llm(messages)
    logger.info(f"[llm]      answer generated ({len(answer)} chars)")

    sources = [
        {
            "source": c["source"],
            "chapter": c["chapter"],
            "section": c["section"],
            "score": c["score"],
        }
        for c in chunks
    ]

    return {"answer": answer, "sources": sources}
