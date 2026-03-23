#!/usr/bin/env python3
"""
Download required GGUF models for TinkerPilot.
Downloads from HuggingFace Hub to the models/ directory.
"""

import os
import sys
import urllib.request
import hashlib
from pathlib import Path

# Model definitions: (filename, url, size_mb_approx)
MODELS = {
    "llm": {
        "filename": "qwen2.5-3b-instruct-q4_k_m.gguf",
        "url": "https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q4_k_m.gguf",
        "size_mb": 2030,
        "description": "Qwen2.5-3B-Instruct (Q4_K_M) - Main LLM for chat, summarization, code explanation",
    },
    "embedding": {
        "filename": "nomic-embed-text-v1.5-Q4_K_M.gguf",
        "url": "https://huggingface.co/nomic-ai/nomic-embed-text-v1.5-GGUF/resolve/main/nomic-embed-text-v1.5.Q4_K_M.gguf",
        "size_mb": 78,
        "description": "Nomic Embed Text v1.5 (Q4_K_M) - Text embeddings for RAG",
    },
}

# faster-whisper downloads its own models automatically, no manual download needed


def get_models_dir() -> Path:
    """Get the models directory path."""
    script_dir = Path(__file__).resolve().parent
    models_dir = script_dir.parent / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    return models_dir


def download_with_progress(url: str, dest: Path, description: str):
    """Download a file with a simple progress indicator."""
    print(f"\n  Downloading: {description}")
    print(f"  URL: {url}")
    print(f"  Destination: {dest}")

    if dest.exists():
        print(f"  Already exists, skipping.")
        return True

    # Use a temp file to avoid partial downloads
    temp_dest = dest.with_suffix(dest.suffix + ".tmp")

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TinkerPilot/0.1"})
        with urllib.request.urlopen(req) as response:
            total = int(response.headers.get("Content-Length", 0))
            downloaded = 0
            block_size = 1024 * 1024  # 1MB chunks

            with open(temp_dest, "wb") as f:
                while True:
                    chunk = response.read(block_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total > 0:
                        pct = (downloaded / total) * 100
                        mb_done = downloaded / (1024 * 1024)
                        mb_total = total / (1024 * 1024)
                        sys.stdout.write(
                            f"\r  Progress: {mb_done:.1f} / {mb_total:.1f} MB ({pct:.1f}%)"
                        )
                        sys.stdout.flush()

        print()  # newline after progress
        temp_dest.rename(dest)
        print(f"  Done.")
        return True

    except Exception as e:
        print(f"\n  ERROR downloading: {e}")
        if temp_dest.exists():
            temp_dest.unlink()
        return False


def main():
    print("=" * 60)
    print("TinkerPilot - Model Downloader")
    print("=" * 60)

    models_dir = get_models_dir()
    print(f"\nModels directory: {models_dir}")

    # Parse args for selective download
    targets = sys.argv[1:] if len(sys.argv) > 1 else list(MODELS.keys())

    # Validate targets
    for t in targets:
        if t not in MODELS:
            print(f"Unknown model: {t}. Available: {', '.join(MODELS.keys())}")
            sys.exit(1)

    # Show plan
    print("\nModels to download:")
    total_size = 0
    for name in targets:
        m = MODELS[name]
        dest = models_dir / m["filename"]
        status = "SKIP (exists)" if dest.exists() else f"~{m['size_mb']} MB"
        if not dest.exists():
            total_size += m["size_mb"]
        print(f"  [{name}] {m['description']} - {status}")

    if total_size == 0:
        print("\nAll models already downloaded.")
        return

    print(f"\nTotal download size: ~{total_size} MB")
    print("Starting downloads...\n")

    # Download
    success = True
    for name in targets:
        m = MODELS[name]
        dest = models_dir / m["filename"]
        if not download_with_progress(m["url"], dest, m["description"]):
            success = False
            print(f"  FAILED to download {name}. You can retry later.")

    print("\n" + "=" * 60)
    if success:
        print("All models downloaded successfully!")
    else:
        print("Some downloads failed. Re-run this script to retry.")

    # Note about whisper
    print("\nNote: Whisper model (for speech-to-text) is downloaded automatically")
    print("by faster-whisper on first use. No manual download needed.")
    print("=" * 60)


if __name__ == "__main__":
    main()
