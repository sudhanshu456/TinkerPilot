"""
Unified search API endpoint.
Searches across documents (ChromaDB), tasks, meetings (SQLite),
and optionally Apple Notes and file system.
"""

import logging
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.db.vector import query_collection
from app.db.sqlite import get_session
from app.db.models import Task, Meeting, Document

logger = logging.getLogger(__name__)
router = APIRouter(tags=["search"])


class SearchRequest(BaseModel):
    query: str
    scope: list[str] = ["documents", "tasks", "meetings"]  # what to search
    limit: int = 10


@router.post("/search")
async def unified_search(req: SearchRequest):
    """Search across all data sources."""
    results = {}

    # 1. Semantic search in documents (ChromaDB)
    if "documents" in req.scope:
        try:
            vector_results = query_collection(req.query, n_results=req.limit)
            docs = vector_results.get("documents", [[]])[0]
            metas = vector_results.get("metadatas", [[]])[0]
            dists = vector_results.get("distances", [[]])[0]

            results["documents"] = [
                {
                    "text": doc[:300] + "..." if len(doc) > 300 else doc,
                    "filename": meta.get("filename", ""),
                    "filepath": meta.get("filepath", ""),
                    "file_type": meta.get("file_type", ""),
                    "relevance": round(1 - dist, 3) if dist else 0,
                    "line_start": meta.get("line_start"),
                }
                for doc, meta, dist in zip(docs, metas, dists)
            ]
        except Exception as e:
            logger.error(f"Document search error: {e}")
            results["documents"] = []

    # 2. Task search (keyword in title/description)
    if "tasks" in req.scope:
        with get_session() as session:
            query_lower = req.query.lower()
            tasks = session.query(Task).all()
            matched = [
                t
                for t in tasks
                if query_lower in (t.title or "").lower()
                or query_lower in (t.description or "").lower()
            ]
            results["tasks"] = [
                {
                    "id": t.id,
                    "title": t.title,
                    "status": t.status,
                    "priority": t.priority,
                }
                for t in matched[: req.limit]
            ]

    # 3. Meeting search (keyword in transcript/title)
    if "meetings" in req.scope:
        with get_session() as session:
            query_lower = req.query.lower()
            meetings = session.query(Meeting).all()
            matched = [
                m
                for m in meetings
                if query_lower in (m.title or "").lower()
                or query_lower in (m.transcript or "").lower()
            ]
            results["meetings"] = [
                {
                    "id": m.id,
                    "title": m.title,
                    "date": m.date,
                    "snippet": _find_snippet(m.transcript, req.query),
                }
                for m in matched[: req.limit]
            ]

    # 4. Apple Notes search (macOS only)
    if "notes" in req.scope:
        from app.config import get_config
        cfg = get_config()
        if cfg.integrations.enable_apple_notes:
            try:
                from app.integrations.apple_notes import search_notes

                results["notes"] = search_notes(req.query, limit=req.limit)
            except Exception as e:
                logger.debug(f"Notes search not available: {e}")
                results["notes"] = []
        else:
            results["notes"] = []

    return {"query": req.query, "results": results}


@router.get("/search")
async def quick_search(q: str, limit: int = 10, file_types: Optional[str] = None):
    """Quick search endpoint (GET for simplicity). file_types is comma-separated."""
    ft = [t.strip() for t in file_types.split(",") if t.strip()] if file_types else None
    req = SearchRequest(query=q, limit=limit, file_types=ft)
    return await unified_search(req)


def _find_snippet(text: str, query: str, window: int = 150) -> str:
    """Find a relevant snippet around the query match."""
    if not text:
        return ""
    idx = text.lower().find(query.lower())
    if idx == -1:
        return text[:300] + "..." if len(text) > 300 else text
    start = max(0, idx - window)
    end = min(len(text), idx + len(query) + window)
    snippet = text[start:end]
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."
    return snippet
