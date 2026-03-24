"""
LLM wrapper using Ollama.
Provides generate and streaming methods via Ollama's local HTTP API.
Model-agnostic: works with any model available in Ollama.
"""

import json
import logging
from typing import Generator, Optional, Union

import httpx

from app.config import get_config

logger = logging.getLogger(__name__)

DEFAULT_SYSTEM_PROMPT = (
    "You are TinkerPilot, a helpful local AI assistant for developers. "
    "Be concise and accurate."
)


def _ollama_url(path: str) -> str:
    """Build an Ollama API URL from config."""
    return f"{get_config().ollama_base_url}{path}"


def _check_ollama():
    """Check if Ollama is running and the model is available."""
    config = get_config()
    try:
        r = httpx.get(_ollama_url("/api/tags"), timeout=5)
        r.raise_for_status()
        models = [m["name"] for m in r.json().get("models", [])]
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
    return get_config().llm.model_name


def unload_llm():
    """No-op for Ollama (server manages model lifecycle)."""
    pass


def _build_messages(
    prompt_or_messages: Union[str, list[dict]],
    system_prompt: Optional[str],
) -> list[dict]:
    """Normalise a single prompt string or a messages list into a full messages list."""
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    if isinstance(prompt_or_messages, str):
        messages.append({"role": "user", "content": prompt_or_messages})
    else:
        messages.extend(prompt_or_messages)
    return messages


def _build_payload(
    messages: list[dict],
    *,
    streaming: bool,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    stop: Optional[list[str]] = None,
) -> dict:
    """Build the Ollama /api/chat payload. Single source of truth for options."""
    config = get_config()
    payload = {
        "model": config.llm.model_name,
        "messages": messages,
        "stream": streaming,
        "options": {
            "temperature": temperature or config.llm.temperature,
            "num_predict": max_tokens or config.llm.max_tokens,
            "top_p": config.llm.top_p,
            "repeat_penalty": config.llm.repeat_penalty,
        },
    }
    if stop:
        payload["options"]["stop"] = stop
    return payload


def generate(
    prompt_or_messages: Union[str, list[dict]],
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    stop: Optional[list[str]] = None,
) -> str:
    """
    Generate a complete response (non-streaming).

    Accepts either a plain prompt string or a conversation-history messages list.
    """
    messages = _build_messages(prompt_or_messages, system_prompt)
    payload = _build_payload(
        messages, streaming=False, max_tokens=max_tokens,
        temperature=temperature, stop=stop,
    )
    r = httpx.post(_ollama_url("/api/chat"), json=payload, timeout=120)
    r.raise_for_status()
    return r.json()["message"]["content"]


# Backward-compatible alias
generate_with_history = generate


def stream(
    prompt_or_messages: Union[str, list[dict]],
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    stop: Optional[list[str]] = None,
) -> Generator[str, None, None]:
    """
    Stream response tokens one at a time.

    Accepts either a plain prompt string or a conversation-history messages list.
    """
    messages = _build_messages(prompt_or_messages, system_prompt)
    payload = _build_payload(
        messages, streaming=True, max_tokens=max_tokens,
        temperature=temperature, stop=stop,
    )
    with httpx.stream(
        "POST", _ollama_url("/api/chat"), json=payload, timeout=120,
    ) as r:
        for line in r.iter_lines():
            if line:
                data = json.loads(line)
                content = data.get("message", {}).get("content", "")
                if content:
                    yield content


# Backward-compatible alias
stream_with_history = stream
