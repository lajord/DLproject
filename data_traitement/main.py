import json
from pathlib import Path
from clean_pdfs import clean_single_pdf
from config import PATHS


def save_output(text: str, metadata: dict, output_dir: str = None):
    if output_dir is None:
        output_dir = PATHS["output_texts"]

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    filename = Path(metadata["filename"]).stem

    text_file = output_path / f"{filename}_cleaned.txt"
    with open(text_file, "w", encoding="utf-8") as f:
        f.write(text)

    metadata_file = output_path / f"{filename}_metadata.json"
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    return text_file, metadata_file


def test_pipeline(pdf_path: str, preview_chunks: int = 5):
    """Clean a single PDF, chunk it, and preview the results."""
    print(f"=== Clean ===")
    text, metadata = clean_single_pdf(pdf_path)
    print(f"Pages       : {metadata['num_pages']}")
    print(f"Chars raw   : {metadata['total_chars_raw']:,}")
    print(f"Chars clean : {metadata['total_chars_cleaned']:,}")
    print(f"Start match : {metadata['content_start_pattern'] or 'none (full text)'}")

    print(f"\n=== Chunks ===")
    from chunk_texts import chunk_text
    source = Path(pdf_path).stem
    chunks = chunk_text(text, source)
    print(f"Total chunks: {len(chunks)}")

    structure = {}
    for c in chunks:
        key = f"{c['chapter']} > {c['section']}" if c['section'] else c['chapter']
        structure[key] = structure.get(key, 0) + 1
    for key, count in list(structure.items())[:15]:
        print(f"  {key:<60} {count} chunks")

    print(f"\n=== Preview ({preview_chunks} first chunks) ===")
    for c in chunks[:preview_chunks]:
        location = f"{c['chapter']}" + (f" > {c['section']}" if c['section'] else "")
        print(f"\n--- [{c['chunk_index']}] {location} ---")
        print(c["text"][:300] + ("..." if len(c["text"]) > 300 else ""))


if __name__ == "__main__":
    import sys
    pdf = sys.argv[1] if len(sys.argv) > 1 else str(Path(PATHS["input_pdfs"]) / "apicius.pdf")
    test_pipeline(pdf)
