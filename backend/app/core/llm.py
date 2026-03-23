"""
LLM wrapper using Ollama.
Provides generate and streaming methods via Ollama's local HTTP API.
Model-agnostic: works with any model available in Ollama.
"""

import json
import logging
from typing import Generator, Optional

import httpx

from app.config import get_config

logger = logging.getLogger(__name__)

OLLAMA_BASE = "http://localhost:11434"


def _check_ollama():
    """Check if Ollama is running and the model is available."""
    config = get_config()
    try:
        r = httpx.get(f"{OLLAMA_BASE}/api/tags", timeout=5)
        r.raise_for_status()
        models = [m["name"] for m in r.json().get("models", [])]
        # Check if our model (or a variant of it) is available
        model = config.llm.model_name
        if not any(model in m for m in models):
            raise RuntimeError(
                f"Model '{model}' not found in Ollama. "
                f"Run: ollama pull {model}\n"
                f"Available models: {', '.join(models) or 'none'}"
            )
    except httpx.ConnectError:
        raise RuntimeError(
            "Ollama is not running. Start it with: ollama serve\nOr install: brew install ollama"
        )


def get_llm():
    """Verify Ollama is ready. Returns the model name."""
    _check_ollama()
    config = get_config()
    return config.llm.model_name


def unload_llm():
    """No-op for Ollama (server manages model lifecycle)."""
    pass


def generate(
    prompt: str,
    system_prompt: str = "You are TinkerPilot, a helpful local AI assistant for developers. Be concise and accurate.",
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    stop: Optional[list[str]] = None,
) -> str:
    """Generate a complete response (non-streaming)."""
    config = get_config()

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": config.llm.model_name,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": temperature or config.llm.temperature,
            "num_predict": max_tokens or config.llm.max_tokens,
            "top_p": config.llm.top_p,
            "repeat_penalty": config.llm.repeat_penalty,
        },
    }
    if stop:
        payload["options"]["stop"] = stop

    r = httpx.post(
        f"{OLLAMA_BASE}/api/chat",
        json=payload,
        timeout=120,
    )
    r.raise_for_status()
    return r.json()["message"]["content"]


def generate_with_history(
    messages: list[dict],
    system_prompt: str = "You are TinkerPilot, a helpful local AI assistant for developers. Be concise and accurate.",
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    stop: Optional[list[str]] = None,
) -> str:
    """Generate a response given a full conversation history."""
    config = get_config()

    full_messages = []
    if system_prompt:
        full_messages.append({"role": "system", "content": system_prompt})
    full_messages.extend(messages)

    payload = {
        "model": config.llm.model_name,
        "messages": full_messages,
        "stream": False,
        "options": {
            "temperature": temperature or config.llm.temperature,
            "num_predict": max_tokens or config.llm.max_tokens,
            "top_p": config.llm.top_p,
            "repeat_penalty": config.llm.repeat_penalty,
        },
    }
    if stop:
        payload["options"]["stop"] = stop

    r = httpx.post(
        f"{OLLAMA_BASE}/api/chat",
        json=payload,
        timeout=120,
    )
    r.raise_for_status()
    return r.json()["message"]["content"]


def stream(
    prompt: str,
    system_prompt: str = "You are TinkerPilot, a helpful local AI assistant for developers. Be concise and accurate.",
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    stop: Optional[list[str]] = None,
) -> Generator[str, None, None]:
    """Stream response tokens one at a time."""
    config = get_config()

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": config.llm.model_name,
        "messages": messages,
        "stream": True,
        "options": {
            "temperature": temperature or config.llm.temperature,
            "num_predict": max_tokens or config.llm.max_tokens,
            "top_p": config.llm.top_p,
            "repeat_penalty": config.llm.repeat_penalty,
        },
    }
    if stop:
        payload["options"]["stop"] = stop

    with httpx.stream(
        "POST",
        f"{OLLAMA_BASE}/api/chat",
        json=payload,
        timeout=120,
    ) as r:
        for line in r.iter_lines():
            if line:
                data = json.loads(line)
                content = data.get("message", {}).get("content", "")
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

    full_messages = []
    if system_prompt:
        full_messages.append({"role": "system", "content": system_prompt})
    full_messages.extend(messages)

    payload = {
        "model": config.llm.model_name,
        "messages": full_messages,
        "stream": True,
        "options": {
            "temperature": temperature or config.llm.temperature,
            "num_predict": max_tokens or config.llm.max_tokens,
            "top_p": config.llm.top_p,
            "repeat_penalty": config.llm.repeat_penalty,
        },
    }
    if stop:
        payload["options"]["stop"] = stop

    with httpx.stream(
        "POST",
        f"{OLLAMA_BASE}/api/chat",
        json=payload,
        timeout=120,
    ) as r:
        for line in r.iter_lines():
            if line:
                data = json.loads(line)
                content = data.get("message", {}).get("content", "")
                if content:
                    yield content
