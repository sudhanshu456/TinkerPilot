"""
LLM wrapper using llama-cpp-python.
Provides singleton model loading with Metal GPU acceleration,
synchronous generate and streaming methods.
Model-agnostic: works with any GGUF model (Qwen, Gemma, Llama, etc.)
"""

import logging
import os
from pathlib import Path
from typing import Generator, Optional

from llama_cpp import Llama

from app.config import get_config

logger = logging.getLogger(__name__)

# Singleton instance
_llm: Optional[Llama] = None
_loaded_model_path: Optional[str] = None


def get_llm() -> Llama:
    """Get or initialize the LLM singleton."""
    global _llm, _loaded_model_path
    config = get_config()

    if _llm is not None and _loaded_model_path == config.llm.model_path:
        return _llm

    model_path = config.llm.model_path
    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"LLM model not found at {model_path}. Run: python scripts/download_models.py"
        )

    logger.info(f"Loading LLM from {model_path}...")
    _llm = Llama(
        model_path=model_path,
        n_ctx=config.llm.n_ctx,
        n_gpu_layers=config.llm.n_gpu_layers,
        n_threads=config.llm.n_threads,
        verbose=config.debug,
    )
    _loaded_model_path = model_path
    logger.info("LLM loaded successfully.")
    return _llm


def unload_llm():
    """Unload the LLM to free memory (e.g., before loading whisper)."""
    global _llm, _loaded_model_path
    if _llm is not None:
        del _llm
        _llm = None
        _loaded_model_path = None
        logger.info("LLM unloaded.")


def generate(
    prompt: str,
    system_prompt: str = "You are TinkerPilot, a helpful local AI assistant for developers. Be concise and accurate.",
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    stop: Optional[list[str]] = None,
) -> str:
    """Generate a complete response (non-streaming)."""
    config = get_config()
    llm = get_llm()

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    response = llm.create_chat_completion(
        messages=messages,
        max_tokens=max_tokens or config.llm.max_tokens,
        temperature=temperature or config.llm.temperature,
        top_p=config.llm.top_p,
        repeat_penalty=config.llm.repeat_penalty,
        stop=stop,
    )

    return response["choices"][0]["message"]["content"]


def generate_with_history(
    messages: list[dict],
    system_prompt: str = "You are TinkerPilot, a helpful local AI assistant for developers. Be concise and accurate.",
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    stop: Optional[list[str]] = None,
) -> str:
    """Generate a response given a full conversation history."""
    config = get_config()
    llm = get_llm()

    full_messages = []
    if system_prompt:
        full_messages.append({"role": "system", "content": system_prompt})
    full_messages.extend(messages)

    response = llm.create_chat_completion(
        messages=full_messages,
        max_tokens=max_tokens or config.llm.max_tokens,
        temperature=temperature or config.llm.temperature,
        top_p=config.llm.top_p,
        repeat_penalty=config.llm.repeat_penalty,
        stop=stop,
    )

    return response["choices"][0]["message"]["content"]


def stream(
    prompt: str,
    system_prompt: str = "You are TinkerPilot, a helpful local AI assistant for developers. Be concise and accurate.",
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    stop: Optional[list[str]] = None,
) -> Generator[str, None, None]:
    """Stream response tokens one at a time."""
    config = get_config()
    llm = get_llm()

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    response = llm.create_chat_completion(
        messages=messages,
        max_tokens=max_tokens or config.llm.max_tokens,
        temperature=temperature or config.llm.temperature,
        top_p=config.llm.top_p,
        repeat_penalty=config.llm.repeat_penalty,
        stop=stop,
        stream=True,
    )

    for chunk in response:
        delta = chunk["choices"][0].get("delta", {})
        content = delta.get("content", "")
        if content:
            yield content


def stream_with_history(
    messages: list[dict],
    system_prompt: str = "You are TinkerPilot, a helpful local AI assistant for developers. Be concise and accurate.",
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    stop: Optional[list[str]] = None,
) -> Generator[str, None, None]:
    """Stream response tokens given a full conversation history."""
    config = get_config()
    llm = get_llm()

    full_messages = []
    if system_prompt:
        full_messages.append({"role": "system", "content": system_prompt})
    full_messages.extend(messages)

    response = llm.create_chat_completion(
        messages=full_messages,
        max_tokens=max_tokens or config.llm.max_tokens,
        temperature=temperature or config.llm.temperature,
        top_p=config.llm.top_p,
        repeat_penalty=config.llm.repeat_penalty,
        stop=stop,
        stream=True,
    )

    for chunk in response:
        delta = chunk["choices"][0].get("delta", {})
        content = delta.get("content", "")
        if content:
            yield content
