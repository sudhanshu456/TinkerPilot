"""
SQLModel database models for TinkerPilot.
Covers documents, meetings, tasks, and chat history.
"""

import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class Document(SQLModel, table=True):
    """Tracks ingested documents for RAG."""

    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str
    filepath: str
    file_type: str  # pdf, md, txt, py, js, csv, json, etc.
    file_size: int = 0
    chunk_count: int = 0
    collection: str = "tinkerpilot_docs"
    created_at: str = Field(default_factory=lambda: datetime.datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.datetime.now().isoformat())


class Meeting(SQLModel, table=True):
    """Meeting transcriptions and summaries."""

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = "Untitled Meeting"
    date: str = Field(default_factory=lambda: datetime.datetime.now().isoformat())
    duration_seconds: float = 0.0
    transcript: str = ""
    summary: str = ""  # JSON string: {summary, decisions, action_items, follow_ups}
    audio_path: Optional[str] = None
    language: str = "en"
    created_at: str = Field(default_factory=lambda: datetime.datetime.now().isoformat())


class Task(SQLModel, table=True):
    """Task/todo items, can be auto-extracted from meetings."""

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: str = ""
    status: str = "todo"  # todo, in_progress, done
    priority: str = "medium"  # low, medium, high
    source_type: Optional[str] = None  # meeting, document, manual
    source_id: Optional[int] = None
    due_date: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.datetime.now().isoformat())


class ChatMessage(SQLModel, table=True):
    """Chat history for conversations."""

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = "default"
    role: str  # user, assistant
    content: str
    sources: str = ""  # JSON string of source references
    created_at: str = Field(default_factory=lambda: datetime.datetime.now().isoformat())
