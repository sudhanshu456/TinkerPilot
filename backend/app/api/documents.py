"""
Document management API endpoints.
Upload, ingest, list, and delete documents for RAG.
"""

import logging
import shutil
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel

from app.config import DATA_DIR
from app.core.rag import ingest_file, ingest_directory, delete_document, list_documents

logger = logging.getLogger(__name__)
router = APIRouter(tags=["documents"])

UPLOAD_DIR = DATA_DIR / "uploads"


class IngestPathRequest(BaseModel):
    path: str
    recursive: bool = True
    collection: Optional[str] = None


@router.post("/documents/upload")
async def upload_and_ingest(
    file: UploadFile = File(...),
    collection: Optional[str] = Form(None),
):
    """Upload a file and ingest it into the RAG pipeline."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    dest = UPLOAD_DIR / file.filename
    with open(dest, "wb") as f:
        content = await file.read()
        f.write(content)

    try:
        result = ingest_file(str(dest), collection_name=collection)
        return {"status": "success", **result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/documents/ingest")
async def ingest_path(req: IngestPathRequest):
    """Ingest a local file or directory by path."""
    path = Path(req.path).expanduser().resolve()

    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Path not found: {req.path}")

    try:
        if path.is_file():
            result = ingest_file(str(path), collection_name=req.collection)
            return {"status": "success", "results": [result]}
        elif path.is_dir():
            results = ingest_directory(
                str(path), recursive=req.recursive, collection_name=req.collection
            )
            return {
                "status": "success",
                "results": results,
                "total_files": len(results),
                "total_chunks": sum(r.get("chunk_count", 0) for r in results),
            }
        else:
            raise HTTPException(status_code=400, detail="Path is neither file nor directory")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


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
