"""
ChromaDB vector store setup for RAG.
Persistent storage at ~/.tinkerpilot/data/chroma/
Uses custom embedding function backed by Ollama embeddings.
"""

import logging
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings

from app.config import DATA_DIR, get_config

logger = logging.getLogger(__name__)

_client: Optional[chromadb.ClientAPI] = None


class OllamaEmbeddingFunction(EmbeddingFunction):
    """Custom ChromaDB embedding function using Ollama."""

    def __call__(self, input: Documents) -> Embeddings:
        from app.core.embeddings import embed_batch

        return embed_batch(input, is_query=False)


def get_chroma_client() -> chromadb.ClientAPI:
    """Get or create the ChromaDB persistent client."""
    global _client
    if _client is not None:
        return _client

    chroma_path = str(DATA_DIR / "chroma")
    Path(chroma_path).mkdir(parents=True, exist_ok=True)

    _client = chromadb.PersistentClient(path=chroma_path)
    logger.info(f"ChromaDB initialized at {chroma_path}")
    return _client


def get_collection(collection_name: Optional[str] = None) -> chromadb.Collection:
    """Get or create a ChromaDB collection with our embedding function."""
    config = get_config()
    name = collection_name or config.rag.collection_name
    client = get_chroma_client()

    collection = client.get_or_create_collection(
        name=name,
        embedding_function=OllamaEmbeddingFunction(),
        metadata={"hnsw:space": "cosine"},
    )
    return collection


def query_collection(
    query_text: str,
    collection_name: Optional[str] = None,
    n_results: int = 5,
    where: Optional[dict] = None,
) -> dict:
    """Query the vector store with a text query.
    Returns dict with ids, documents, metadatas, distances."""
    from app.core.embeddings import embed_query

    config = get_config()
    name = collection_name or config.rag.collection_name
    client = get_chroma_client()

    collection = client.get_or_create_collection(
        name=name,
        embedding_function=OllamaEmbeddingFunction(),
        metadata={"hnsw:space": "cosine"},
    )

    # Embed query
    query_embedding = embed_query(query_text)

    kwargs = {
        "query_embeddings": [query_embedding],
        "n_results": min(n_results, collection.count()) if collection.count() > 0 else n_results,
    }
    if where:
        kwargs["where"] = where

    if collection.count() == 0:
        return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}

    results = collection.query(**kwargs)
    return results
