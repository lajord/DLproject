SYSTEM_PROMPT = """You are an expert on ancient Rome and classical antiquity.
Answer the user's question using ONLY the context provided below.
If the answer cannot be found in the context, say: "I don't have enough information in my sources to answer this question."
Always be precise and cite which source your answer comes from."""


def build_prompt(question: str, chunks: list[dict]) -> list[dict]:
    """Build the messages list for the OpenAI chat API."""
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        source_label = chunk["source"]
        if chunk.get("section"):
            source_label += f" > {chunk['section']}"
        context_parts.append(f"[{i}] ({source_label})\n{chunk['text']}")

    context = "\n\n".join(context_parts)

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion: {question}",
        },
    ]
