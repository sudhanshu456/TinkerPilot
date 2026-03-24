"""
Obsidian vault integration.
Reads markdown files from an Obsidian vault directory,
indexes them into ChromaDB for semantic search.
"""

import logging
from pathlib import Path
from typing import Optional

from app.config import get_config

logger = logging.getLogger(__name__)


def get_vault_path() -> Optional[Path]:
    """Get configured Obsidian vault path."""
    config = get_config()
    vault = config.integrations.obsidian_vault_path
    if vault:
        p = Path(vault).expanduser().resolve()
        if p.is_dir():
            return p
    return None


def list_notes(vault_path: Optional[str] = None) -> list[dict]:
    """List all markdown files in the Obsidian vault."""
    if vault_path:
        vault = Path(vault_path).expanduser().resolve()
    else:
        vault = get_vault_path()

    if not vault or not vault.is_dir():
        return []

    notes = []
    for md_file in sorted(vault.rglob("*.md")):
        # Skip hidden dirs and Obsidian internals
        rel = md_file.relative_to(vault)
        if any(part.startswith(".") for part in rel.parts):
            continue

        stat = md_file.stat()
        notes.append(
            {
                "title": md_file.stem,
                "path": str(md_file),
                "relative_path": str(rel),
                "folder": str(rel.parent) if rel.parent != Path(".") else "",
                "size": stat.st_size,
                "modified": stat.st_mtime,
            }
        )

    return notes


def read_note(filepath: str) -> dict:
    """Read a single Obsidian note."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Note not found: {filepath}")

    content = path.read_text(encoding="utf-8", errors="replace")

    return {
        "title": path.stem,
        "path": str(path),
        "content": content,
        "size": len(content),
    }


def search_notes_keyword(
    query: str, vault_path: Optional[str] = None, limit: int = 10
) -> list[dict]:
    """Simple keyword search across Obsidian notes."""
    notes = list_notes(vault_path)
    query_lower = query.lower()
    results = []

    for note_meta in notes:
        try:
            path = Path(note_meta["path"])
            content = path.read_text(encoding="utf-8", errors="replace")

            if query_lower in content.lower() or query_lower in note_meta["title"].lower():
                # Find snippet
                idx = content.lower().find(query_lower)
                if idx >= 0:
                    start = max(0, idx - 100)
                    end = min(len(content), idx + len(query) + 100)
                    snippet = content[start:end]
                    if start > 0:
                        snippet = "..." + snippet
                    if end < len(content):
                        snippet += "..."
                else:
                    snippet = content[:200]

                results.append(
                    {
                        **note_meta,
                        "snippet": snippet,
                    }
                )

                if len(results) >= limit:
                    break
        except Exception as e:
            logger.debug(f"Error reading {note_meta['path']}: {e}")
            continue

    return results


def index_vault(vault_path: Optional[str] = None, collection_name: Optional[str] = None) -> dict:
    """Index all Obsidian notes into the RAG pipeline."""
    from app.core.rag import ingest_file

    if vault_path:
        vault = Path(vault_path).expanduser().resolve()
    else:
        vault = get_vault_path()

    if not vault or not vault.is_dir():
        return {"error": "Vault path not configured or not found", "indexed": 0}

    results = []
    for md_file in sorted(vault.rglob("*.md")):
        rel = md_file.relative_to(vault)
        if any(part.startswith(".") for part in rel.parts):
            continue
        try:
            result = ingest_file(str(md_file), collection_name=collection_name)
            results.append(result)
        except Exception as e:
            logger.error(f"Error indexing {md_file}: {e}")
            results.append({"filename": md_file.name, "error": str(e)})

    return {
        "indexed": len([r for r in results if r.get("chunk_count", 0) > 0]),
        "total_files": len(results),
        "total_chunks": sum(r.get("chunk_count", 0) for r in results),
        "results": results,
    }
