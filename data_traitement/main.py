import json
from pathlib import Path
from clean_pdfs import clean_single_pdf, clean_multiple_pdfs
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


if __name__ == "__main__":
    results = clean_multiple_pdfs(PATHS["input_pdfs"])

    print(f"\n=== Résumé ===")
    for text, metadata in results:
        if "error" not in metadata:
            save_output(text, metadata)
            print(f"{metadata['filename']}: {metadata['total_chars_cleaned']:,} chars, pattern={metadata['content_start_pattern'] or 'none'}")
