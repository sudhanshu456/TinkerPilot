"""
Daily Digest API endpoint.
Aggregates pending tasks, recent meetings, and notes
into a single AI-generated morning briefing.
"""

import json
import logging
import time
import threading
from typing import Optional

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel

from app.db.sqlite import get_session
from app.db.models import Task, Meeting

logger = logging.getLogger(__name__)
router = APIRouter(tags=["digest"])

CACHE_TTL = 1800  # 30 minutes
_digest_cache = {
    "text": None,
    "raw": None,
    "timestamp": 0
}
_generation_lock = threading.Lock()


def _get_briefing_type():
    import datetime
    hour = datetime.datetime.now().hour
    if hour < 12:
        return "morning briefing"
    elif hour < 17:
        return "afternoon update"
    return "evening wrap-up"


def _gather_raw_data(include_slow: bool = False):
    """Gathers the fast, structured database information instantly."""
    sections = {}

    # 1. Pending tasks
    with get_session() as session:
        pending_tasks = (
            session.query(Task)
            .filter(Task.status.in_(["todo", "in_progress"]))
            .order_by(Task.priority.desc())
            .limit(20)
            .all()
        )
        sections["tasks"] = [
            {"title": t.title, "status": t.status, "priority": t.priority, "due": t.due_date}
            for t in pending_tasks
        ]

    # 2. Recent meetings
    with get_session() as session:
        recent_meetings = session.query(Meeting).order_by(Meeting.date.desc()).limit(5).all()
        sections["recent_meetings"] = []
        for m in recent_meetings:
            summary = {}
            if m.summary:
                try:
                    summary = json.loads(m.summary)
                except json.JSONDecodeError:
                    summary = {"summary": m.summary}
            sections["recent_meetings"].append(
                {
                    "title": m.title,
                    "date": m.date,
                    "summary": summary.get("summary", "No summary")
                }
            )

    # 3. Apple Notes (Slow osascript call)
    notes = []
    if include_slow:
        try:
            from app.integrations.apple_notes import get_notes
            notes = get_notes(limit=5)
            for n in notes:
                if "id" in n:
                    del n["id"]
                if "folder" in n:
                    del n["folder"]
        except Exception as e:
            logger.debug(f"Apple Notes not available: {e}")
    
    sections["notes"] = notes

    return sections


def _generate_force(briefing_type: str, raw_data: dict):
    """The slow, synchronous LLM network task."""
    import datetime
    from app.core.llm import generate
    now = datetime.datetime.now()

    context = json.dumps(raw_data, indent=2, default=str)
    prompt = f"""Based on the following data, create a concise {briefing_type} for a developer.
It is currently {now.strftime("%I:%M %p on %A, %B %d, %Y")}.
Include: high-priority tasks to focus on, follow-ups from recent meetings, and any relevant notes.
Keep it practical and actionable, under 300 words.

Data:
{context}"""

    digest_text = generate(
        prompt,
        system_prompt=(
            f"You are TinkerPilot, generating a {briefing_type}. "
            "Be concise, practical, and prioritize actionable items. "
            "Use markdown formatting with headers and bullet points."
        ),
        temperature=0.4,
    )
    return digest_text


def _run_locked_generation():
    with _generation_lock:
        try:
            # Check cache again inside lock just in case it was created while waiting
            if time.time() - _digest_cache["timestamp"] < CACHE_TTL and _digest_cache["text"]:
                 return
            
            b_type = _get_briefing_type()
            raw = _gather_raw_data(include_slow=True)
            text = _generate_force(b_type, raw)
            
            _digest_cache["text"] = text
            _digest_cache["raw"] = raw
            _digest_cache["timestamp"] = time.time()
        except Exception as e:
            logger.error(f"Failed to generate digest asynchronously: {e}")


def prewarm_digest():
    """Background task to pre-generate the digest on server startup."""
    try:
        logger.info("Pre-warming daily digest in background...")
        _run_locked_generation()
        logger.info("Daily digest pre-warmed successfully (Cached!)")
    except Exception as e:
        logger.error(f"Failed to pre-warm daily digest: {e}")


@router.get("/digest")
async def get_daily_digest():
    """Generate or retrieve a daily digest instantly without blocking the UI."""
    
    # 1. Fast Path: Use Cache!
    if time.time() - _digest_cache["timestamp"] < CACHE_TTL and _digest_cache["text"]:
        return {
            "digest": _digest_cache["text"],
            "raw": _digest_cache["raw"],
            "cached": True
        }
    
    # 2. Grab only the fast SQLite database information instantly
    raw = _gather_raw_data(include_slow=False)

    # 3. Offload the slow 10-second LLM generation to an explicit, detached background thread!
    # Do NOT use FastAPI BackgroundTasks, because Starlette keeps the HTTP socket alive
    # until the background tasks finish, which causes the frontend fetch() to infinitely hang!
    if not _generation_lock.locked():
        threading.Thread(target=_run_locked_generation, daemon=True).start()
    
    # 4. Return instantly to the UI!
    return {
        "digest": "🤖 The AI is currently analyzing your data to generate your morning briefing. Check back in a few moments!",
        "raw": raw,
        "cached": False
    }
