"""
RAG (Retrieval-Augmented Generation) pipeline.
Handles document ingestion, embedding, storage, and context-aware querying.
"""

import json
import logging
import os
from pathlib import Path
from typing import Generator, Optional

from app.config import get_config
from app.core.parsers import parse_file, is_supported, SUPPORTED_EXTENSIONS
from app.core.chunker import chunk_text
from app.db.vector import get_collection, query_collection
from app.db.sqlite import get_session
from app.db.models import Document

logger = logging.getLogger(__name__)


def ingest_file(filepath: str, collection_name: Optional[str] = None, tag: Optional[str] = None) -> dict:
    """
    Ingest a single file into the RAG pipeline.
    Parse -> Chunk -> Embed -> Store in ChromaDB + SQLite.

    Returns dict with document_id, chunk_count, filename.
    """
    path = Path(filepath).resolve()
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    if not is_supported(str(path)):
        raise ValueError(f"Unsupported file type: {path.suffix}")

    config = get_config()
    col_name = collection_name or config.rag.collection_name

    logger.info(f"Ingesting: {path.name}")

    # Parse the file
    parsed = parse_file(str(path))
    content = parsed["content"]
    metadata = parsed["metadata"]

    if not content.strip():
        logger.warning(f"Empty content from {path.name}, skipping.")
        return {"document_id": None, "chunk_count": 0, "filename": path.name}

    # Chunk the content
    chunks = chunk_text(content, metadata=metadata)
    logger.info(f"  Created {len(chunks)} chunks from {path.name}")

    if not chunks:
        return {"document_id": None, "chunk_count": 0, "filename": path.name}

    # Store in ChromaDB
    collection = get_collection(col_name)

    ids = []
    documents = []
    metadatas = []

    for i, chunk in enumerate(chunks):
        chunk_id = f"{path.stem}_{i}_{hash(path.name) % 100000}"
        ids.append(chunk_id)
        documents.append(chunk["text"])
        # ChromaDB metadata must be flat (str, int, float, bool)
        flat_meta = {
            "filename": metadata["filename"],
            "filepath": metadata["filepath"],
            "file_type": metadata["file_type"],
            "chunk_index": i,
            "total_chunks": len(chunks),
        }
        if "line_start" in chunk["metadata"]:
            flat_meta["line_start"] = chunk["metadata"]["line_start"]
        if "line_end" in chunk["metadata"]:
            flat_meta["line_end"] = chunk["metadata"]["line_end"]
        if tag:
            flat_meta["tag"] = tag
        metadatas.append(flat_meta)

    # Upsert (handles re-ingestion)
    collection.upsert(ids=ids, documents=documents, metadatas=metadatas)

    # Record in SQLite
    with get_session() as session:
        # Check if already exists
        existing = session.query(Document).filter(Document.filepath == str(path)).first()

        if existing:
            existing.chunk_count = len(chunks)
            existing.file_size = metadata.get("file_size", 0)
            import datetime

            existing.updated_at = datetime.datetime.now().isoformat()
            session.add(existing)
            session.commit()
            doc_id = existing.id
        else:
            doc = Document(
                filename=path.name,
                filepath=str(path),
                file_type=metadata["file_type"],
                file_size=metadata.get("file_size", 0),
                chunk_count=len(chunks),
                collection=col_name,
            )
            session.add(doc)
            session.commit()
            session.refresh(doc)
            doc_id = doc.id

    logger.info(f"  Ingested {path.name}: {len(chunks)} chunks, doc_id={doc_id}")
    return {"document_id": doc_id, "chunk_count": len(chunks), "filename": path.name}


def ingest_directory(
    dirpath: str,
    recursive: bool = True,
    collection_name: Optional[str] = None,
    tag: Optional[str] = None,
) -> list[dict]:
    """Ingest all supported files from a directory."""
    path = Path(dirpath).resolve()
    if not path.is_dir():
        raise NotADirectoryError(f"Not a directory: {dirpath}")

    results = []
    pattern = "**/*" if recursive else "*"

    for fpath in sorted(path.glob(pattern)):
        if fpath.is_file() and is_supported(str(fpath)):
            # Skip hidden files and common non-content directories
            parts = fpath.relative_to(path).parts
            if any(
                p.startswith(".")
                or p
                in (
                    "node_modules",
                    "__pycache__",
                    "venv",
                    ".venv",
                    "dist",
                    "build",
                    ".git",
                    ".next",
                )
                for p in parts
            ):
                continue
            try:
                result = ingest_file(str(fpath), collection_name, tag)
                results.append(result)
            except Exception as e:
                logger.error(f"Error ingesting {fpath}: {e}")
                results.append(
                    {
                        "document_id": None,
                        "chunk_count": 0,
                        "filename": fpath.name,
                        "error": str(e),
                    }
                )

    return results


def query_rag(
    question: str,
    collection_name: Optional[str] = None,
    top_k: Optional[int] = None,
) -> dict:
    """
    Query the RAG pipeline. Retrieves relevant chunks and generates
    an answer using the LLM with context.

    Returns dict with: answer, sources, context_chunks
    """
    from app.core.llm import generate

    config = get_config()
    k = top_k or config.rag.top_k

    # Retrieve relevant chunks
    results = query_collection(question, collection_name, n_results=k)

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    if not documents:
        # No context found, answer from general knowledge
        answer = generate(
            question,
            system_prompt=(
                "You are TinkerPilot, a helpful AI assistant for developers. "
                "The user asked a question but no relevant documents were found in the knowledge base. "
                "Answer based on your general knowledge, and note that no local documents matched."
            ),
        )
        return {"answer": answer, "sources": [], "context_chunks": []}

    # Build context
    context_parts = []
    sources = []
    for i, (doc, meta, dist) in enumerate(zip(documents, metadatas, distances)):
        source_ref = meta.get("filename", "unknown")
        if "line_start" in meta:
            source_ref += f":{meta['line_start']}"
            if "line_end" in meta:
                source_ref += f"-{meta['line_end']}"

        context_parts.append(f"[Source {i + 1}: {source_ref}]\n{doc}")
        sources.append(
            {
                "index": i + 1,
                "filename": meta.get("filename", "unknown"),
                "filepath": meta.get("filepath", ""),
                "file_type": meta.get("file_type", ""),
                "chunk_index": meta.get("chunk_index", 0),
                "line_start": meta.get("line_start"),
                "line_end": meta.get("line_end"),
                "relevance": round(1 - dist, 3) if dist else 0,
            }
        )

    context = "\n\n---\n\n".join(context_parts)

    system_prompt = (
        "You are TinkerPilot, a helpful AI assistant for developers. "
        "Answer the user's question based on the provided context from their local documents. "
        "Cite sources using [Source N] notation. "
        "If the context doesn't contain enough information, say so and provide what you can. "
        "Be concise and accurate."
    )

    prompt = f"Context from local documents:\n\n{context}\n\n---\n\nQuestion: {question}"

    answer = generate(prompt, system_prompt=system_prompt)

    return {
        "answer": answer,
        "sources": sources,
        "context_chunks": [
            {"text": doc, "metadata": meta} for doc, meta in zip(documents, metadatas)
        ],
    }


def stream_rag(
    question: str,
    collection_name: Optional[str] = None,
    top_k: Optional[int] = None,
) -> tuple[Generator[str, None, None], list[dict]]:
    """
    Stream RAG response. Returns (token_generator, sources).
    Sources are available immediately, tokens stream as generated.
    """
    from app.core.llm import stream

    config = get_config()
    k = top_k or config.rag.top_k

    results = query_collection(question, collection_name, n_results=k)

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    sources = []
    if not documents:
        gen = stream(
            question,
            system_prompt=(
                "You are TinkerPilot, a helpful AI assistant for developers. "
                "No relevant documents found in the knowledge base. "
                "Answer based on general knowledge and note that no local documents matched."
            ),
        )
        return gen, sources

    context_parts = []
    for i, (doc, meta, dist) in enumerate(zip(documents, metadatas, distances)):
        source_ref = meta.get("filename", "unknown")
        if "line_start" in meta:
            source_ref += f":{meta['line_start']}"

        context_parts.append(f"[Source {i + 1}: {source_ref}]\n{doc}")
        sources.append(
            {
                "index": i + 1,
                "filename": meta.get("filename", "unknown"),
                "filepath": meta.get("filepath", ""),
                "file_type": meta.get("file_type", ""),
                "chunk_index": meta.get("chunk_index", 0),
                "line_start": meta.get("line_start"),
                "line_end": meta.get("line_end"),
                "relevance": round(1 - dist, 3) if dist else 0,
            }
        )

    context = "\n\n---\n\n".join(context_parts)

    system_prompt = (
        "You are TinkerPilot, a helpful AI assistant for developers. "
        "Answer the user's question based on the provided context from their local documents. "
        "Cite sources using [Source N] notation. Be concise and accurate."
    )

    prompt = f"Context from local documents:\n\n{context}\n\n---\n\nQuestion: {question}"

    gen = stream(prompt, system_prompt=system_prompt)
    return gen, sources


def delete_document(document_id: int, collection_name: Optional[str] = None) -> bool:
    """Delete a document and its chunks from both SQLite and ChromaDB."""
    config = get_config()
    col_name = collection_name or config.rag.collection_name

    with get_session() as session:
        doc = session.get(Document, document_id)
        if not doc:
            return False

        # Delete from ChromaDB
        collection = get_collection(col_name)
        # Get all chunk IDs for this document
        try:
            results = collection.get(
                where={"filepath": doc.filepath},
            )
            if results["ids"]:
                collection.delete(ids=results["ids"])
        except Exception as e:
            logger.error(f"Error deleting chunks from ChromaDB: {e}")

        # Delete from SQLite
        session.delete(doc)
        session.commit()

    return True


def list_documents() -> list[dict]:
    """List all ingested documents."""
    with get_session() as session:
        docs = session.query(Document).order_by(Document.created_at.desc()).all()
        return [
            {
                "id": d.id,
                "filename": d.filename,
                "filepath": d.filepath,
                "file_type": d.file_type,
                "file_size": d.file_size,
                "chunk_count": d.chunk_count,
                "created_at": d.created_at,
                "updated_at": d.updated_at,
            }
            for d in docs
        ]
