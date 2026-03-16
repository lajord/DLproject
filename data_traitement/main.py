import json
import sys
from pathlib import Path
from clean_pdfs import clean_single_pdf
from chunk_texts import chunk_text
from ingest_chromadb import ingest_chunks
from config import PATHS


def step_clean(pdf_path: str):
    text, metadata = clean_single_pdf(pdf_path)
    print(f"[clean] {metadata['num_pages']} pages | {metadata['total_chars_cleaned']:,} chars | match: {metadata['content_start_pattern'] or 'none'}")
    return text, metadata


def step_chunk(text: str, source: str):
    chunks = chunk_text(text, source)
    print(f"[chunk] {len(chunks)} chunks generated")
    return chunks


def step_ingest(chunks: list):
    ingest_chunks(chunks)


if __name__ == "__main__":
    pdf = sys.argv[1] if len(sys.argv) > 1 else str(Path(PATHS["input_pdfs"]) / "apicius.pdf")
    source = Path(pdf).stem

    text, metadata = step_clean(pdf)
    chunks        = step_chunk(text, source)
    step_ingest(chunks)
