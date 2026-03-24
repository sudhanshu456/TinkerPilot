"""
TinkerPilot configuration.
All paths default to ~/.tinkerpilot/ for user data.
Models are managed by Ollama (LLM + embeddings) and auto-downloaded (STT + TTS).
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

import yaml

# Base directories
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent  # TinkerPilot/
USER_DATA_DIR = Path.home() / ".tinkerpilot"
DATA_DIR = USER_DATA_DIR / "data"


@dataclass
class LLMConfig:
    model_name: str = "qwen2.5:3b"
    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: float = 0.9
    repeat_penalty: float = 1.1


@dataclass
class EmbeddingConfig:
    model_name: str = "qwen3-embedding:0.6b"
    embedding_dim: int = 1024


@dataclass
class STTConfig:
    """Speech-to-text config (Moonshine Voice)."""

    model_size: str = "small"  # tiny, small, medium
    language: str = "en"
    # Legacy keys kept for backward compatibility
    device: str = "cpu"
    compute_type: str = "int8"
    beam_size: int = 5
    vad_filter: bool = True


@dataclass
class TTSConfig:
    """Text-to-speech config (Kokoro-82M)."""

    voice: str = "af_heart"  # Default voice
    speed: float = 1.0
    lang_code: str = "a"  # a=American English, b=British


@dataclass
class RAGConfig:
    chunk_size: int = 512
    chunk_overlap: int = 50
    top_k: int = 5
    collection_name: str = "tinkerpilot_docs"


@dataclass
class IntegrationConfig:
    obsidian_vault_path: Optional[str] = None
    watch_directories: list = field(default_factory=list)
    enable_apple_notes: bool = True


@dataclass
class AppConfig:
    llm: LLMConfig = field(default_factory=LLMConfig)
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    stt: STTConfig = field(default_factory=STTConfig)
    tts: TTSConfig = field(default_factory=TTSConfig)
    rag: RAGConfig = field(default_factory=RAGConfig)
    integrations: IntegrationConfig = field(default_factory=IntegrationConfig)
    ollama_base_url: str = "http://localhost:11434"
    hf_token: Optional[str] = None
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = False


def load_config(config_path: Optional[str] = None) -> AppConfig:
    """Load config from YAML file, falling back to defaults."""
    if config_path is None:
        config_path = str(USER_DATA_DIR / "config.yaml")

    config = AppConfig()

    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            data = yaml.safe_load(f) or {}

        section_map = {
            "llm": config.llm,
            "embedding": config.embedding,
            "stt": config.stt,
            "whisper": config.stt,  # backward compatibility alias
            "tts": config.tts,
            "rag": config.rag,
            "integrations": config.integrations,
        }
        for section_name, section_obj in section_map.items():
            if section_name in data:
                for k, v in data[section_name].items():
                    if hasattr(section_obj, k):
                        setattr(section_obj, k, v)

        for k in ("host", "port", "debug", "ollama_base_url", "hf_token"):
            if k in data:
                setattr(config, k, data[k])

    return config


def ensure_directories():
    """Create required directories if they don't exist."""
    for d in [
        USER_DATA_DIR,
        DATA_DIR,
        DATA_DIR / "chroma",
        DATA_DIR / "audio",
        DATA_DIR / "uploads",
    ]:
        d.mkdir(parents=True, exist_ok=True)


_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    global _config
    if _config is None:
        ensure_directories()
        _config = load_config()
    return _config
