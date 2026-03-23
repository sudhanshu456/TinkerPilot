"""
Embedding wrapper using Ollama.
Uses nomic-embed-text for generating text embeddings locally via Ollama API.
Embeddings are used for RAG (semantic search over documents).
"""

import logging
from typing import Optional

import httpx

from app.config import get_config

logger = logging.getLogger(__name__)

OLLAMA_BASE = "http://localhost:11434"


def _embed_via_ollama(text: str, model: Optional[str] = None) -> list[float]:
    """Call Ollama embeddings API for a single text."""
    config = get_config()
    model_name = model or config.embedding.model_name

    r = httpx.post(
        f"{OLLAMA_BASE}/api/embed",
        json={"model": model_name, "input": text},
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    # Ollama returns {"embeddings": [[...], ...]}
    return data["embeddings"][0]


def _embed_batch_via_ollama(texts: list[str], model: Optional[str] = None) -> list[list[float]]:
    """Call Ollama embeddings API for a batch of texts."""
    config = get_config()
    model_name = model or config.embedding.model_name

    r = httpx.post(
        f"{OLLAMA_BASE}/api/embed",
        json={"model": model_name, "input": texts},
        timeout=60,
    )
    r.raise_for_status()
    data = r.json()
    return data["embeddings"]


def get_embedder():
    """Verify Ollama embedding model is available. Returns model name."""
    config = get_config()
    return config.embedding.model_name


def unload_embedder():
    """No-op for Ollama (server manages model lifecycle)."""
    pass


def embed_text(text: str) -> list[float]:
    """Generate embedding vector for a single text string."""
    # nomic-embed-text in Ollama handles prefixes internally
    return _embed_via_ollama(text)


def embed_query(query: str) -> list[float]:
    """Generate embedding vector for a search query."""
    return _embed_via_ollama(query)


def embed_batch(texts: list[str], is_query: bool = False) -> list[list[float]]:
    """Generate embeddings for a batch of texts."""
    if not texts:
        return []

    # Process in batches to avoid timeouts on large sets
    batch_size = 32
    results = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        batch_results = _embed_batch_via_ollama(batch)
        results.extend(batch_results)

    return results
