"""
Document parsers for various file formats.
Extracts text content from PDFs, markdown, code, plaintext, CSV, JSON, DOCX.
"""

import csv
import io
import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# File extensions mapped to parser types
SUPPORTED_EXTENSIONS = {
    # Documents
    ".pdf": "pdf",
    ".md": "markdown",
    ".markdown": "markdown",
    ".txt": "text",
    ".rst": "text",
    ".docx": "docx",
    # Code
    ".py": "code",
    ".js": "code",
    ".ts": "code",
    ".tsx": "code",
    ".jsx": "code",
    ".java": "code",
    ".go": "code",
    ".rs": "code",
    ".c": "code",
    ".cpp": "code",
    ".h": "code",
    ".hpp": "code",
    ".rb": "code",
    ".php": "code",
    ".swift": "code",
    ".kt": "code",
    ".scala": "code",
    ".sh": "code",
    ".bash": "code",
    ".zsh": "code",
    ".fish": "code",
    ".sql": "code",
    ".r": "code",
    ".lua": "code",
    ".vim": "code",
    ".el": "code",
    # Config
    ".yaml": "text",
    ".yml": "text",
    ".toml": "text",
    ".ini": "text",
    ".cfg": "text",
    ".conf": "text",
    ".env": "text",
    ".properties": "text",
    # Data
    ".csv": "csv",
    ".json": "json",
    ".jsonl": "jsonl",
    ".xml": "text",
    ".html": "text",
    ".htm": "text",
    # Logs
    ".log": "text",
}


def get_file_type(filepath: str) -> Optional[str]:
    """Get the parser type for a file based on extension."""
    ext = Path(filepath).suffix.lower()
    return SUPPORTED_EXTENSIONS.get(ext)


def is_supported(filepath: str) -> bool:
    """Check if a file type is supported for parsing."""
    return get_file_type(filepath) is not None


def parse_file(filepath: str) -> dict:
    """
    Parse a file and extract its text content.

    Returns:
        dict with keys:
            - content: extracted text
            - metadata: dict with filename, filepath, file_type, pages (if PDF)
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    file_type = get_file_type(filepath)
    if file_type is None:
        raise ValueError(f"Unsupported file type: {path.suffix}")

    metadata = {
        "filename": path.name,
        "filepath": str(path.resolve()),
        "file_type": file_type,
        "file_size": path.stat().st_size,
    }

    parsers = {
        "pdf": _parse_pdf,
        "markdown": _parse_text,
        "text": _parse_text,
        "code": _parse_code,
        "csv": _parse_csv,
        "json": _parse_json,
        "jsonl": _parse_jsonl,
        "docx": _parse_docx,
    }

    parser = parsers.get(file_type)
    if parser is None:
        raise ValueError(f"No parser for type: {file_type}")

    content = parser(filepath)
    metadata["char_count"] = len(content)

    return {"content": content, "metadata": metadata}


def _parse_pdf(filepath: str) -> str:
    """Extract text from PDF using PyMuPDF."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise ImportError("PyMuPDF required: pip install PyMuPDF")

    doc = fitz.open(filepath)
    pages = []
    for page_num, page in enumerate(doc, 1):
        text = page.get_text()
        if text.strip():
            pages.append(f"[Page {page_num}]\n{text.strip()}")
    doc.close()
    return "\n\n".join(pages)


def _parse_text(filepath: str) -> str:
    """Read plain text / markdown files."""
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def _parse_code(filepath: str) -> str:
    """Read code files with language annotation."""
    path = Path(filepath)
    lang = path.suffix.lstrip(".")
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    return f"[File: {path.name}] [Language: {lang}]\n\n{content}"


def _parse_csv(filepath: str) -> str:
    """Parse CSV into readable text format."""
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        rows = list(reader)

    if not rows:
        return ""

    # Format as table-like text
    header = rows[0] if rows else []
    lines = [f"CSV file with {len(rows) - 1} rows and {len(header)} columns."]
    lines.append(f"Columns: {', '.join(header)}")
    lines.append("")

    # Include up to 100 rows in the parsed content
    for i, row in enumerate(rows[:101], 0):
        if i == 0:
            lines.append("| " + " | ".join(row) + " |")
            lines.append("|" + "|".join(["---"] * len(row)) + "|")
        else:
            lines.append("| " + " | ".join(row) + " |")

    if len(rows) > 101:
        lines.append(f"... and {len(rows) - 101} more rows")

    return "\n".join(lines)


def _parse_json(filepath: str) -> str:
    """Parse JSON into readable text."""
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        data = json.load(f)

    # Pretty print with truncation for large files
    text = json.dumps(data, indent=2, ensure_ascii=False)
    if len(text) > 50000:
        text = text[:50000] + "\n... [truncated, file too large]"
    return f"JSON file contents:\n{text}"


def _parse_jsonl(filepath: str) -> str:
    """Parse JSONL (one JSON object per line)."""
    lines_out = []
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if line:
                lines_out.append(f"Line {i}: {line}")
            if i > 200:
                lines_out.append(f"... truncated at 200 lines")
                break

    return f"JSONL file with entries:\n" + "\n".join(lines_out)


def _parse_docx(filepath: str) -> str:
    """Parse DOCX files."""
    try:
        from docx import Document
    except ImportError:
        raise ImportError("python-docx required: pip install python-docx")

    doc = Document(filepath)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)
