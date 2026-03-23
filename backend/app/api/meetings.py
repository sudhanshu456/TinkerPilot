"""
Meeting transcription and summarization API endpoints.
"""

import json
import logging
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel

from app.config import DATA_DIR
from app.db.sqlite import get_session
from app.db.models import Meeting, Task

logger = logging.getLogger(__name__)
router = APIRouter(tags=["meetings"])

AUDIO_DIR = DATA_DIR / "audio"


SUMMARIZE_PROMPT = """Analyze the following meeting transcript and provide a structured summary.

Transcript:
{transcript}

Provide your response in the following JSON format (and ONLY this JSON, no other text):
{{
    "summary": "A concise 2-4 sentence overview of the meeting",
    "key_topics": ["topic1", "topic2"],
    "decisions": ["decision1", "decision2"],
    "action_items": [
        {{"task": "description", "assignee": "person or unknown", "priority": "high/medium/low"}}
    ],
    "follow_ups": ["follow up item 1", "follow up item 2"]
}}"""


class MeetingSummaryRequest(BaseModel):
    transcript: str
    title: str = "Untitled Meeting"


@router.post("/meetings/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    title: Optional[str] = None,
    language: Optional[str] = None,
):
    """Upload an audio file, transcribe it, and generate a summary."""
    from app.core.whisper_stt import transcribe_file

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    # Save uploaded audio
    suffix = Path(file.filename).suffix or ".wav"
    audio_path = AUDIO_DIR / f"{file.filename}"
    with open(audio_path, "wb") as f:
        content = await file.read()
        f.write(content)

    try:
        # Transcribe
        result = transcribe_file(str(audio_path), language=language)
        transcript = result["text"]

        if not transcript.strip():
            raise HTTPException(status_code=400, detail="No speech detected in audio")

        # Summarize
        summary_data = _summarize_transcript(transcript)

        # Calculate duration from segments
        segments = result.get("segments", [])
        duration = segments[-1]["end"] if segments else 0

        # Save to database
        with get_session() as session:
            meeting = Meeting(
                title=title or file.filename,
                duration_seconds=duration,
                transcript=transcript,
                summary=json.dumps(summary_data),
                audio_path=str(audio_path),
                language=result.get("language", "en"),
            )
            session.add(meeting)
            session.commit()
            session.refresh(meeting)

            # Auto-create tasks from action items
            _create_tasks_from_summary(session, meeting.id, summary_data)

            return {
                "meeting_id": meeting.id,
                "transcript": transcript,
                "summary": summary_data,
                "segments": segments,
                "language": result.get("language"),
                "duration_seconds": duration,
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@router.post("/meetings/summarize")
async def summarize_transcript(req: MeetingSummaryRequest):
    """Summarize a provided transcript text (no audio upload needed)."""
    summary_data = _summarize_transcript(req.transcript)

    with get_session() as session:
        meeting = Meeting(
            title=req.title,
            transcript=req.transcript,
            summary=json.dumps(summary_data),
        )
        session.add(meeting)
        session.commit()
        session.refresh(meeting)

        _create_tasks_from_summary(session, meeting.id, summary_data)

        return {
            "meeting_id": meeting.id,
            "summary": summary_data,
        }


@router.get("/meetings")
async def list_meetings():
    """List all meetings."""
    with get_session() as session:
        meetings = session.query(Meeting).order_by(Meeting.date.desc()).all()
        return {
            "meetings": [
                {
                    "id": m.id,
                    "title": m.title,
                    "date": m.date,
                    "duration_seconds": m.duration_seconds,
                    "language": m.language,
                    "has_summary": bool(m.summary),
                    "created_at": m.created_at,
                }
                for m in meetings
            ]
        }


@router.get("/meetings/{meeting_id}")
async def get_meeting(meeting_id: int):
    """Get a specific meeting with transcript and summary."""
    with get_session() as session:
        meeting = session.get(Meeting, meeting_id)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")

        return {
            "id": meeting.id,
            "title": meeting.title,
            "date": meeting.date,
            "duration_seconds": meeting.duration_seconds,
            "transcript": meeting.transcript,
            "summary": json.loads(meeting.summary) if meeting.summary else None,
            "language": meeting.language,
            "created_at": meeting.created_at,
        }


@router.delete("/meetings/{meeting_id}")
async def delete_meeting(meeting_id: int):
    """Delete a meeting."""
    with get_session() as session:
        meeting = session.get(Meeting, meeting_id)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")

        # Delete audio file if exists
        if meeting.audio_path:
            Path(meeting.audio_path).unlink(missing_ok=True)

        session.delete(meeting)
        session.commit()
    return {"status": "deleted", "meeting_id": meeting_id}


def _summarize_transcript(transcript: str) -> dict:
    """Generate structured summary from transcript using LLM."""
    from app.core.llm import generate

    prompt = SUMMARIZE_PROMPT.format(transcript=transcript[:8000])  # Limit context

    response = generate(
        prompt,
        system_prompt="You are a meeting summarizer. Output ONLY valid JSON, no other text.",
        temperature=0.3,
    )

    # Parse JSON from response
    try:
        # Try to extract JSON from the response
        text = response.strip()
        # Handle markdown code blocks
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        return json.loads(text)
    except json.JSONDecodeError:
        logger.warning("Failed to parse summary JSON, returning raw text")
        return {
            "summary": response,
            "key_topics": [],
            "decisions": [],
            "action_items": [],
            "follow_ups": [],
        }


def _create_tasks_from_summary(session, meeting_id: int, summary_data: dict):
    """Auto-create tasks from meeting action items."""
    action_items = summary_data.get("action_items", [])
    for item in action_items:
        if isinstance(item, dict):
            title = item.get("task", str(item))
            priority = item.get("priority", "medium")
        else:
            title = str(item)
            priority = "medium"

        task = Task(
            title=title,
            description=f"From meeting #{meeting_id}",
            status="todo",
            priority=priority,
            source_type="meeting",
            source_id=meeting_id,
        )
        session.add(task)
    session.commit()
