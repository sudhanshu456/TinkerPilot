"""
SQLite database setup using SQLModel.
Stores structured data: documents, meetings, tasks, chat history.
"""

import logging
from pathlib import Path
from typing import Optional

from sqlmodel import SQLModel, Session, create_engine

from app.config import DATA_DIR

logger = logging.getLogger(__name__)

_engine = None


def get_db_path() -> str:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return str(DATA_DIR / "tinkerpilot.db")


def get_engine():
    global _engine
    if _engine is None:
        db_path = get_db_path()
        _engine = create_engine(
            f"sqlite:///{db_path}",
            echo=False,
            connect_args={"check_same_thread": False},
        )
        logger.info(f"SQLite database at {db_path}")
    return _engine


def init_db():
    """Create all tables if they don't exist."""
    from app.db.models import Document, Meeting, Task, ChatMessage  # noqa: F401

    engine = get_engine()
    SQLModel.metadata.create_all(engine)
    logger.info("Database tables initialized.")


def get_session() -> Session:
    """Get a new database session."""
    return Session(get_engine())
