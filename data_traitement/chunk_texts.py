import re
from pathlib import Path
from typing import List, Dict, Tuple

CHUNK_SIZE = 2400   # ~600 tokens
OVERLAP = 400       # ~100 tokens
MIN_CHUNK = 200     # drop/merge below this


# ── Heading detection ────────────────────────────────────────────────────────

_CHAPTER_PATTERNS = [
    r'^(?:CHAPTER|Chapter)\s+(?:\d+|[IVXLCDM]+)(?:\s*[.:\-\u2013\u2014].*)?$',
    r'^(?:PART|Part|BOOK|Book)\s+(?:\d+|[IVXLCDM]+)(?:\s*[.:\-\u2013\u2014].*)?$',
    r'^[IVXLCDM]{1,6}\.\s*(?:[.:\-\u2013\u2014].*)?$',
    r'^\d{1,2}\.\s*(?:[.:\-\u2013\u2014].*)?$',
]


def _is_chapter_heading(line: str) -> bool:
    s = line.strip()
    if not s or len(s) > 120:
        return False
    for p in _CHAPTER_PATTERNS:
        if re.match(p, s, re.IGNORECASE):
            return True
    return False


def _looks_like_section_heading(line: str, prev_line: str, next_line: str) -> bool:
    """
    Detect free-form section titles like 'Historical background' or 'Dining in Rome'.
    Two signals:
      - strong: line is adjacent to a blank line
      - medium: at least half the words are capitalised (Title Case)
    Both must combine with basic shape checks.
    """
    s = line.strip()
    if not s or len(s) > 70 or len(s) < 3:
        return False
    if not s[0].isupper():
        return False
    if s[-1] in '.!?,;':
        return False
    if re.search(r'\.{3,}', s):          # TOC dots
        return False
    if re.search(r'[\s.]{2,}\d+\s*$', s):  # ends with page number
        return False
    words = s.split()
    if len(words) > 10:
        return False

    adj_blank = (not prev_line.strip()) or (not next_line.strip())
    cap_ratio = sum(1 for w in words if w and w[0].isupper()) / len(words)
    is_title_cased = cap_ratio >= 0.5

    return adj_blank or is_title_cased


# ── Structure parsing ─────────────────────────────────────────────────────────

def _parse_sections(text: str) -> List[Dict]:
    """
    Parse text line by line into sections.
    Returns list of {"chapter": str, "section": str, "body": str}.
    """
    lines = text.split('\n')
    sections: List[Dict] = []
    current_chapter = "preamble"
    current_section = ""
    body: List[str] = []

    def flush():
        content = '\n'.join(body).strip()
        if content:
            sections.append({
                "chapter": current_chapter,
                "section": current_section,
                "body": content,
            })
        body.clear()

    for i, line in enumerate(lines):
        prev = lines[i - 1] if i > 0 else ""
        nxt  = lines[i + 1] if i < len(lines) - 1 else ""

        if _is_chapter_heading(line):
            flush()
            current_chapter = line.strip()
            current_section = ""

        elif _looks_like_section_heading(line, prev, nxt):
            flush()
            current_section = line.strip()

        else:
            body.append(line)

    flush()
    return sections


# ── Chunking helpers ──────────────────────────────────────────────────────────

def _split_sentences(text: str) -> List[str]:
    parts = re.split(r'(?<=[.!?])\s+(?=[A-Z"\'])', text)
    return [s.strip() for s in parts if s.strip()]


def _chunk_paragraph(paragraph: str, chunk_size: int, overlap: int) -> List[str]:
    """Break an oversized paragraph into sentence-boundary chunks with overlap."""
    sentences = _split_sentences(paragraph)
    chunks: List[str] = []
    current: List[str] = []
    current_len = 0

    for sentence in sentences:
        s_len = len(sentence)
        if current_len + s_len > chunk_size and current:
            chunks.append(' '.join(current))
            overlap_sents: List[str] = []
            acc = 0
            for s in reversed(current):
                if acc + len(s) <= overlap:
                    overlap_sents.insert(0, s)
                    acc += len(s)
                else:
                    break
            current = overlap_sents + [sentence]
            current_len = sum(len(s) for s in current)
        else:
            current.append(sentence)
            current_len += s_len

    if current:
        chunks.append(' '.join(current))
    return chunks


def _merge_and_chunk(paragraphs: List[str], chunk_size: int, overlap: int) -> List[str]:
    """Merge small paragraphs and split large ones."""
    raw: List[str] = []
    current = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if len(para) > chunk_size:
            if current:
                raw.append(current)
                current = ""
            raw.extend(_chunk_paragraph(para, chunk_size, overlap))
        elif len(current) + len(para) + 2 > chunk_size:
            raw.append(current)
            current = para
        else:
            current = (current + "\n\n" + para).strip() if current else para

    if current:
        raw.append(current)

    # Add overlap between consecutive chunks at a sentence boundary
    final: List[str] = []
    for i, chunk in enumerate(raw):
        if i > 0:
            tail = raw[i - 1][-overlap:]
            boundary = tail.find('. ')
            if boundary != -1:
                tail = tail[boundary + 2:]
            chunk = tail.strip() + ' ' + chunk
        final.append(chunk.strip())

    return final


# ── Public API ────────────────────────────────────────────────────────────────

def chunk_text(text: str, source: str, chunk_size: int = CHUNK_SIZE,
               overlap: int = OVERLAP, min_chunk: int = MIN_CHUNK) -> List[Dict]:
    """
    Chunk a cleaned book text into RAG-ready chunks.

    Each chunk dict:
        text        — chunk content
        source      — book filename stem
        chapter     — nearest chapter heading above
        section     — nearest section/subsection heading above
        chunk_index — global index across the whole book
    """
    sections = _parse_sections(text)
    all_chunks: List[Dict] = []
    chunk_index = 0

    for sec in sections:
        if not sec["body"].strip():
            continue

        paragraphs = re.split(r'\n{2,}', sec["body"])
        chunks = _merge_and_chunk(paragraphs, chunk_size, overlap)

        for chunk in chunks:
            if len(chunk.strip()) < min_chunk:
                continue
            all_chunks.append({
                "text": chunk.strip(),
                "source": source,
                "chapter": sec["chapter"],
                "section": sec["section"],
                "chunk_index": chunk_index,
            })
            chunk_index += 1

    return all_chunks


def chunk_multiple_texts(cleaned_dir: str, chunk_size: int = CHUNK_SIZE,
                         overlap: int = OVERLAP, min_chunk: int = MIN_CHUNK) -> List[Dict]:
    """Process all *_cleaned.txt files in a directory."""
    all_chunks: List[Dict] = []

    for txt_file in Path(cleaned_dir).glob("*_cleaned.txt"):
        source = txt_file.stem.replace("_cleaned", "")
        text = txt_file.read_text(encoding="utf-8")
        chunks = chunk_text(text, source, chunk_size, overlap, min_chunk)
        all_chunks.extend(chunks)
        print(f"OK {txt_file.name}: {len(chunks)} chunks")

    return all_chunks
