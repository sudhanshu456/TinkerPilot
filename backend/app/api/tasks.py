"""
Task management API endpoints.
CRUD for tasks, auto-extraction from meetings.
"""

import datetime
import json
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db.sqlite import get_session
from app.db.models import Task

logger = logging.getLogger(__name__)
router = APIRouter(tags=["tasks"])


class TaskCreate(BaseModel):
    title: str
    description: str = ""
    status: str = "todo"
    priority: str = "medium"
    due_date: Optional[str] = None
    source_type: Optional[str] = None
    source_id: Optional[int] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[str] = None


@router.post("/tasks")
async def create_task(req: TaskCreate):
    """Create a new task."""
    with get_session() as session:
        task = Task(
            title=req.title,
            description=req.description,
            status=req.status,
            priority=req.priority,
            due_date=req.due_date,
            source_type=req.source_type,
            source_id=req.source_id,
        )
        session.add(task)
        session.commit()
        session.refresh(task)
        return _task_to_dict(task)


@router.get("/tasks")
async def list_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
):
    """List tasks with optional filters."""
    with get_session() as session:
        query = session.query(Task)
        if status:
            query = query.filter(Task.status == status)
        if priority:
            query = query.filter(Task.priority == priority)
        tasks = query.order_by(Task.created_at.desc()).all()
        return {"tasks": [_task_to_dict(t) for t in tasks], "total": len(tasks)}


@router.get("/tasks/{task_id}")
async def get_task(task_id: int):
    """Get a specific task."""
    with get_session() as session:
        task = session.get(Task, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return _task_to_dict(task)


@router.put("/tasks/{task_id}")
async def update_task(task_id: int, req: TaskUpdate):
    """Update a task."""
    with get_session() as session:
        task = session.get(Task, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        if req.title is not None:
            task.title = req.title
        if req.description is not None:
            task.description = req.description
        if req.status is not None:
            task.status = req.status
        if req.priority is not None:
            task.priority = req.priority
        if req.due_date is not None:
            task.due_date = req.due_date

        task.updated_at = datetime.datetime.now().isoformat()
        session.add(task)
        session.commit()
        session.refresh(task)
        return _task_to_dict(task)


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: int):
    """Delete a task."""
    with get_session() as session:
        task = session.get(Task, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        session.delete(task)
        session.commit()
    return {"status": "deleted", "task_id": task_id}


@router.post("/tasks/extract")
async def extract_tasks_from_text(text: str):
    """Extract action items from arbitrary text using LLM."""
    from app.core.llm import generate

    prompt = f"""Extract action items / tasks from the following text.
Return ONLY a JSON array of objects with keys: "task", "priority" (high/medium/low).
If no tasks found, return an empty array [].

Text:
{text[:4000]}"""

    response = generate(
        prompt,
        system_prompt="You extract action items from text. Output ONLY valid JSON array.",
        temperature=0.2,
    )

    try:
        raw = response.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
        items = json.loads(raw)
    except json.JSONDecodeError:
        items = []

    # Create tasks
    created = []
    with get_session() as session:
        for item in items:
            if isinstance(item, dict) and "task" in item:
                task = Task(
                    title=item["task"],
                    priority=item.get("priority", "medium"),
                    source_type="extracted",
                )
                session.add(task)
                session.commit()
                session.refresh(task)
                created.append(_task_to_dict(task))

    return {"tasks": created, "total": len(created)}


def _task_to_dict(task: Task) -> dict:
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "priority": task.priority,
        "source_type": task.source_type,
        "source_id": task.source_id,
        "due_date": task.due_date,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
    }
