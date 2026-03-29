from sentence_transformers import CrossEncoder

_model = None
MODEL_NAME = "BAAI/bge-reranker-base"


def _get_model() -> CrossEncoder:
    global _model
    if _model is None:
        _model = CrossEncoder(MODEL_NAME)
    return _model


def rerank(question: str, chunks: list[dict], top_k: int = 5) -> list[dict]:
    """Rerank chunks using cross-encoder and return top_k most relevant."""
    model = _get_model()

    pairs = [(question, c["text"]) for c in chunks]
    scores = model.predict(pairs)

    for chunk, score in zip(chunks, scores):
        chunk["rerank_score"] = round(float(score), 4)

    ranked = sorted(chunks, key=lambda c: c["rerank_score"], reverse=True)
    return ranked[:top_k]
