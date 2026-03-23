#!/usr/bin/env python3
"""
Pull required Ollama models for TinkerPilot.
This is a convenience wrapper — setup.sh already handles this.
"""

import subprocess
import sys


MODELS = [
    {
        "name": "qwen2.5:3b",
        "description": "Qwen2.5 3B — main LLM for chat, summarization, code explanation",
        "size": "~2.0 GB",
    },
    {
        "name": "qwen3-embedding:0.6b",
        "description": "Qwen3 Embedding 0.6B — text embeddings for RAG, code retrieval, 32K context",
        "size": "~639 MB",
    },
]


def check_ollama():
    """Verify Ollama is installed and running."""
    try:
        result = subprocess.run(
            ["ollama", "list"], capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0
    except FileNotFoundError:
        print("ERROR: Ollama is not installed.")
        print("Install it with: brew install ollama")
        return False
    except subprocess.TimeoutExpired:
        print("ERROR: Ollama is not responding. Start it with: ollama serve")
        return False


def pull_model(name: str):
    """Pull a model via Ollama."""
    print(f"  Pulling {name}...")
    result = subprocess.run(["ollama", "pull", name], timeout=600)
    return result.returncode == 0


def main():
    print("=" * 50)
    print("TinkerPilot - Model Setup (via Ollama)")
    print("=" * 50)

    if not check_ollama():
        sys.exit(1)

    # Check which models are already pulled
    result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
    installed = result.stdout if result.returncode == 0 else ""

    print("\nModels needed:")
    for m in MODELS:
        status = "INSTALLED" if m["name"] in installed else m["size"]
        print(f"  [{m['name']}] {m['description']} — {status}")

    print()
    for m in MODELS:
        if m["name"] not in installed:
            if not pull_model(m["name"]):
                print(f"  FAILED to pull {m['name']}")
                sys.exit(1)
            print(f"  {m['name']} ready.")
        else:
            print(f"  {m['name']} already installed, skipping.")

    print("\n" + "=" * 50)
    print("All models ready!")
    print("Note: Whisper (speech-to-text) downloads automatically on first use.")
    print("=" * 50)


if __name__ == "__main__":
    main()
