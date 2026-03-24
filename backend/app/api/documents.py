"""
Document management API endpoints.
Upload, ingest, list, and delete documents for RAG.
"""

import logging
import shutil
import threading
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel

from app.config import DATA_DIR
from app.core.rag import ingest_file, ingest_directory, delete_document, list_documents

logger = logging.getLogger(__name__)
router = APIRouter(tags=["documents"])

UPLOAD_DIR = DATA_DIR / "uploads"

# In-memory store for background ingestion jobs
_ingest_jobs: dict[str, dict] = {}


class IngestPathRequest(BaseModel):
    path: str
    recursive: bool = True
    collection: Optional[str] = None


def _run_ingest_job(job_id: str, path: Path, recursive: bool, collection: Optional[str]):
    """Background worker for ingestion."""
    try:
        if path.is_file():
            result = ingest_file(str(path), collection_name=collection)
            _ingest_jobs[job_id].update(
                status="done", results=[result],
                total_files=1, total_chunks=result.get("chunk_count", 0),
            )
        elif path.is_dir():
            results = ingest_directory(str(path), recursive=recursive, collection_name=collection)
            _ingest_jobs[job_id].update(
                status="done", results=results,
                total_files=len(results),
                total_chunks=sum(r.get("chunk_count", 0) for r in results),
            )
    except Exception as e:
        logger.error(f"Background ingest failed for {path}: {e}")
        _ingest_jobs[job_id].update(status="error", error=str(e))


@router.post("/documents/upload")
async def upload_and_ingest(
    file: UploadFile = File(...),
    collection: Optional[str] = Form(None),
):
    """Upload a file and ingest it into the RAG pipeline (background)."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    dest = UPLOAD_DIR / file.filename
    with open(dest, "wb") as f:
        content = await file.read()
        f.write(content)

    job_id = str(uuid.uuid4())[:8]
    _ingest_jobs[job_id] = {"status": "running", "path": str(dest)}
    threading.Thread(
        target=_run_ingest_job, args=(job_id, dest, False, collection), daemon=True,
    ).start()

    return {"status": "accepted", "job_id": job_id, "filename": file.filename}


@router.post("/documents/ingest")
async def ingest_path(req: IngestPathRequest):
    """Ingest a local file or directory by path (background)."""
    path = Path(req.path).expanduser().resolve()

    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Path not found: {req.path}")

    job_id = str(uuid.uuid4())[:8]
    _ingest_jobs[job_id] = {"status": "running", "path": str(path)}
    threading.Thread(
        target=_run_ingest_job,
        args=(job_id, path, req.recursive, req.collection),
        daemon=True,
    ).start()

    return {"status": "accepted", "job_id": job_id, "path": str(path)}


@router.get("/documents/ingest/{job_id}")
async def ingest_status(job_id: str):
    """Check the status of a background ingestion job."""
    job = _ingest_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job_id": job_id, **job}


@router.get("/documents")
async def get_documents():
    """List all ingested documents."""
    docs = list_documents()
    return {"documents": docs, "total": len(docs)}


@router.delete("/documents/{document_id}")
async def remove_document(document_id: int):
    """Delete a document and its chunks."""
    success = delete_document(document_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"status": "deleted", "document_id": document_id}
