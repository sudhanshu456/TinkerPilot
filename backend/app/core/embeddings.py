"""
Embedding wrapper using llama-cpp-python.
Uses nomic-embed-text-v1.5 GGUF for generating text embeddings locally.
Embeddings are used for RAG (semantic search over documents).
"""

import logging
import os
from typing import Optional

from llama_cpp import Llama

from app.config import get_config

logger = logging.getLogger(__name__)

_embedder: Optional[Llama] = None
_loaded_path: Optional[str] = None


def get_embedder() -> Llama:
    """Get or initialize the embedding model singleton."""
    global _embedder, _loaded_path
    config = get_config()

    if _embedder is not None and _loaded_path == config.embedding.model_path:
        return _embedder

    model_path = config.embedding.model_path
    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Embedding model not found at {model_path}. Run: python scripts/download_models.py"
        )

    logger.info(f"Loading embedding model from {model_path}...")
    _embedder = Llama(
        model_path=model_path,
        n_ctx=config.embedding.n_ctx,
        n_gpu_layers=config.embedding.n_gpu_layers,
        embedding=True,
        verbose=False,
    )
    _loaded_path = model_path
    logger.info("Embedding model loaded successfully.")
    return _embedder


def unload_embedder():
    """Unload embedding model to free memory."""
    global _embedder, _loaded_path
    if _embedder is not None:
        del _embedder
        _embedder = None
        _loaded_path = None
        logger.info("Embedding model unloaded.")


def embed_text(text: str) -> list[float]:
    """Generate embedding vector for a single text string."""
    embedder = get_embedder()
    # nomic-embed-text requires a task prefix for best results
    prefixed = f"search_document: {text}"
    result = embedder.embed(prefixed)
    # llama-cpp-python returns list of lists for embed()
    if isinstance(result[0], list):
        return result[0]
    return result


def embed_query(query: str) -> list[float]:
    """Generate embedding vector for a search query.
    Uses 'search_query:' prefix as recommended by nomic-embed-text."""
    embedder = get_embedder()
    prefixed = f"search_query: {query}"
    result = embedder.embed(prefixed)
    if isinstance(result[0], list):
        return result[0]
    return result


def embed_batch(texts: list[str], is_query: bool = False) -> list[list[float]]:
    """Generate embeddings for a batch of texts."""
    embedder = get_embedder()
    prefix = "search_query: " if is_query else "search_document: "
    prefixed = [f"{prefix}{t}" for t in texts]

    results = []
    # Process in small batches to avoid OOM on 8GB machine
    batch_size = 32
    for i in range(0, len(prefixed), batch_size):
        batch = prefixed[i : i + batch_size]
        batch_results = embedder.embed(batch)
        # Normalize the result shape
        for r in batch_results:
            if isinstance(r, list):
                results.append(r)
            else:
                results.append([r])

    return results
