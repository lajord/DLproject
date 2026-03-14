import pdfplumber
import re
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime
from config import CLEAN_CONFIG


def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def find_content_start(text: str, patterns: List[str]) -> Tuple[int, str]:
    normalized = normalize_text(text)

    for pattern in patterns:
        pattern_normalized = normalize_text(pattern)
        match = re.search(r'\b' + re.escape(pattern_normalized) + r'\b', normalized)

        if match:
            start_pos = match.start()
            original_pos = 0
            normalized_count = 0

            for i, char in enumerate(text):
                if normalized_count >= start_pos:
                    original_pos = i
                    break
                if not char.isspace() or char == ' ':
                    normalized_count += 1

            return original_pos, pattern

    return 0, ""


def clean_single_pdf(pdf_path: str, config: Dict = None) -> Tuple[str, Dict]:
    if config is None:
        config = CLEAN_CONFIG

    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF non trouvé: {pdf_path}")

    with pdfplumber.open(pdf_path) as pdf:
        metadata = {
            "filename": pdf_path.name,
            "filepath": str(pdf_path),
            "title": pdf.metadata.get("Title", ""),
            "author": pdf.metadata.get("Author", ""),
            "num_pages": len(pdf.pages),
            "extraction_date": datetime.now().isoformat(),
        }

        full_text = ""
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                full_text += page_text + "\n"

        metadata["total_chars_raw"] = len(full_text)

        patterns = config["content_start_patterns"]
        start_index, found_pattern = find_content_start(full_text, patterns)

        cleaned_text = full_text[start_index:].strip()

        if len(cleaned_text) < config["min_content_length"]:
            cleaned_text = full_text.strip()
            start_index = 0
            found_pattern = ""

        metadata["content_start_index"] = start_index
        metadata["content_start_pattern"] = found_pattern
        metadata["total_chars_cleaned"] = len(cleaned_text)

        return cleaned_text, metadata


def clean_multiple_pdfs(pdf_dir: str, config: Dict = None) -> List[Tuple[str, Dict]]:
    if config is None:
        config = CLEAN_CONFIG

    pdf_dir = Path(pdf_dir)
    if not pdf_dir.exists():
        raise FileNotFoundError(f"Répertoire non trouvé: {pdf_dir}")

    pdf_files = list(pdf_dir.glob("*.pdf"))
    results = []

    for pdf_path in pdf_files:
        try:
            text, metadata = clean_single_pdf(str(pdf_path), config)
            results.append((text, metadata))
            print(f"OK {pdf_path.name}")
        except Exception as e:
            print(f"ERREUR {pdf_path.name}: {e}")
            results.append(("", {"error": str(e), "filepath": str(pdf_path)}))

    return results
