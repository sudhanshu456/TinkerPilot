"""
TinkerPilot configuration.
All paths default to ~/.tinkerpilot/ for user data.
Models are stored in the project's models/ directory.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

import yaml


# Base directories
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent  # TinkerPilot/
USER_DATA_DIR = Path.home() / ".tinkerpilot"
MODELS_DIR = PROJECT_ROOT / "models"
DATA_DIR = USER_DATA_DIR / "data"


@dataclass
class LLMConfig:
    model_path: str = ""
    n_ctx: int = 4096
    n_gpu_layers: int = -1  # -1 = offload all to Metal GPU
    n_threads: int = 4
    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: float = 0.9
    repeat_penalty: float = 1.1


@dataclass
class EmbeddingConfig:
    model_path: str = ""
    n_ctx: int = 2048
    n_gpu_layers: int = -1
    embedding_dim: int = 768


@dataclass
class WhisperConfig:
    model_size: str = "small"
    device: str = "cpu"
    compute_type: str = "int8"
    language: str = "en"
    beam_size: int = 5
    vad_filter: bool = True


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
    enable_apple_calendar: bool = True
    enable_apple_notes: bool = True


@dataclass
class AppConfig:
    llm: LLMConfig = field(default_factory=LLMConfig)
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    whisper: WhisperConfig = field(default_factory=WhisperConfig)
    rag: RAGConfig = field(default_factory=RAGConfig)
    integrations: IntegrationConfig = field(default_factory=IntegrationConfig)
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = False

    def __post_init__(self):
        if not self.llm.model_path:
            self.llm.model_path = str(MODELS_DIR / "qwen2.5-3b-instruct-q4_k_m.gguf")
        if not self.embedding.model_path:
            self.embedding.model_path = str(MODELS_DIR / "nomic-embed-text-v1.5-Q4_K_M.gguf")


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
            "whisper": config.whisper,
            "rag": config.rag,
            "integrations": config.integrations,
        }
        for section_name, section_obj in section_map.items():
            if section_name in data:
                for k, v in data[section_name].items():
                    if hasattr(section_obj, k):
                        setattr(section_obj, k, v)

        for k in ("host", "port", "debug"):
            if k in data:
                setattr(config, k, data[k])

    return config


def ensure_directories():
    """Create required directories if they don't exist."""
    for d in [
        USER_DATA_DIR,
        DATA_DIR,
        MODELS_DIR,
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
