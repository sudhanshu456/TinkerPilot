"""
Text chunking for RAG pipeline.
Splits documents into overlapping chunks for embedding and retrieval.
Code-aware splitting for source files.
"""

import logging
import re
from typing import Optional

from app.config import get_config

logger = logging.getLogger(__name__)


def chunk_text(
    text: str,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
    metadata: Optional[dict] = None,
) -> list[dict]:
    """
    Split text into overlapping chunks.

    Returns list of dicts: {text, metadata}
    metadata includes chunk_index and any passed-through metadata.
    """
    config = get_config()
    size = chunk_size or config.rag.chunk_size
    overlap = chunk_overlap or config.rag.chunk_overlap
    meta = metadata or {}

    if not text.strip():
        return []

    file_type = meta.get("file_type", "text")

    if file_type == "code":
        return _chunk_code(text, size, overlap, meta)

    return _chunk_recursive(text, size, overlap, meta)


def _chunk_recursive(
    text: str,
    chunk_size: int,
    overlap: int,
    metadata: dict,
) -> list[dict]:
    """
    Recursive text splitter. Tries to split on natural boundaries:
    paragraphs > sentences > words > characters.
    """
    # Approximate tokens as chars / 4
    char_size = chunk_size * 4
    char_overlap = overlap * 4

    separators = ["\n\n", "\n", ". ", " ", ""]

    chunks = _split_recursive(text, separators, char_size, char_overlap)

    results = []
    for i, chunk_text in enumerate(chunks):
        chunk_meta = {**metadata, "chunk_index": i, "total_chunks": len(chunks)}
        results.append({"text": chunk_text.strip(), "metadata": chunk_meta})

    return [r for r in results if r["text"]]


def _split_recursive(
    text: str,
    separators: list[str],
    chunk_size: int,
    overlap: int,
) -> list[str]:
    """Recursively split text using a hierarchy of separators."""
    if len(text) <= chunk_size:
        return [text] if text.strip() else []

    sep = separators[0] if separators else ""
    remaining_seps = separators[1:] if len(separators) > 1 else [""]

    if sep == "":
        # Last resort: hard split by characters
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunks.append(text[start:end])
            start = end - overlap if end < len(text) else end
        return chunks

    parts = text.split(sep)

    current_chunk = ""
    chunks = []

    for part in parts:
        test = current_chunk + sep + part if current_chunk else part

        if len(test) <= chunk_size:
            current_chunk = test
        else:
            if current_chunk:
                # If current chunk is still too big, split it further
                if len(current_chunk) > chunk_size:
                    sub_chunks = _split_recursive(
                        current_chunk, remaining_seps, chunk_size, overlap
                    )
                    chunks.extend(sub_chunks)
                else:
                    chunks.append(current_chunk)

            current_chunk = part

    if current_chunk:
        if len(current_chunk) > chunk_size:
            sub_chunks = _split_recursive(current_chunk, remaining_seps, chunk_size, overlap)
            chunks.extend(sub_chunks)
        else:
            chunks.append(current_chunk)

    # Apply overlap
    if overlap > 0 and len(chunks) > 1:
        overlapped = [chunks[0]]
        for i in range(1, len(chunks)):
            prev = chunks[i - 1]
            overlap_text = prev[-overlap:] if len(prev) > overlap else prev
            overlapped.append(overlap_text + sep + chunks[i])
        chunks = overlapped

    return chunks


def _chunk_code(
    text: str,
    chunk_size: int,
    overlap: int,
    metadata: dict,
) -> list[dict]:
    """
    Code-aware chunking. Splits on function/class boundaries first,
    then falls back to line-based splitting.
    """
    char_size = chunk_size * 4
    lines = text.split("\n")

    # Try to find natural code boundaries
    boundaries = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if any(
            stripped.startswith(kw)
            for kw in [
                "def ",
                "class ",
                "function ",
                "async function ",
                "export function ",
                "export default ",
                "export class ",
                "fn ",
                "func ",
                "pub fn ",
                "pub func ",
                "public ",
                "private ",
                "protected ",
                "# ---",
                "// ---",
                "/* ---",
            ]
        ):
            boundaries.append(i)

    if not boundaries:
        # No clear boundaries, fall back to line-based chunks
        boundaries = list(range(0, len(lines), max(1, char_size // 80)))

    # Make sure we start at 0
    if boundaries[0] != 0:
        boundaries.insert(0, 0)

    chunks = []
    for idx in range(len(boundaries)):
        start = boundaries[idx]
        end = boundaries[idx + 1] if idx + 1 < len(boundaries) else len(lines)

        chunk_lines = lines[start:end]
        chunk_text = "\n".join(chunk_lines)

        # If chunk is too large, split it further
        if len(chunk_text) > char_size * 2:
            sub_chunks = _chunk_recursive(chunk_text, chunk_size, overlap, metadata)
            for sc in sub_chunks:
                sc["metadata"]["line_start"] = start + 1
            chunks.extend(sub_chunks)
        else:
            chunk_meta = {
                **metadata,
                "chunk_index": len(chunks),
                "line_start": start + 1,
                "line_end": end,
            }
            if chunk_text.strip():
                chunks.append({"text": chunk_text.strip(), "metadata": chunk_meta})

    # Update chunk indices
    for i, chunk in enumerate(chunks):
        chunk["metadata"]["chunk_index"] = i
        chunk["metadata"]["total_chunks"] = len(chunks)

    return chunks
