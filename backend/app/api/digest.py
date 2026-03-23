"""
Daily Digest API endpoint.
Aggregates pending tasks, recent meetings, and notes
into a single AI-generated morning briefing.
"""

import json
import logging
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.db.sqlite import get_session
from app.db.models import Task, Meeting

logger = logging.getLogger(__name__)
router = APIRouter(tags=["digest"])


@router.get("/digest")
async def get_daily_digest():
    """Generate a daily digest with tasks, meetings, and notes."""
    from app.core.llm import generate

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

    # 2. Recent meetings (last 3 days)
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
                    "summary": summary.get("summary", "No summary"),
                }
            )

    # 3. Recent Apple Notes
    notes = []
    try:
        from app.integrations.apple_notes import get_notes

        notes = get_notes(limit=5)
        # Clean up the output so the LLM doesn't see or print internal Apple coredata IDs
        for n in notes:
            if "id" in n:
                del n["id"]
            if "folder" in n:
                del n["folder"]
    except Exception as e:
        logger.debug(f"Apple Notes not available: {e}")
    sections["notes"] = notes

    # 4. Generate digest with LLM
    context = json.dumps(sections, indent=2, default=str)

    prompt = f"""Based on the following data, create a concise daily briefing for a developer.
Include: high-priority tasks to focus on, follow-ups from recent meetings, and any relevant notes.
Keep it practical and actionable, under 300 words.

Data:
{context}"""

    digest_text = generate(
        prompt,
        system_prompt=(
            "You are TinkerPilot, generating a morning briefing. "
            "Be concise, practical, and prioritize actionable items. "
            "Use markdown formatting with headers and bullet points."
        ),
        temperature=0.4,
    )

    return {
        "digest": digest_text,
        "raw": sections,
    }
