---
title: Getting Started
sidebar_position: 2
---
Installating TinkerPilot take one single command, and it will install all the dependencies and tools required for TinkerPilot to run, that too within less than 10 minutes, depending on your internet speed and your computer's performance.

## What you need

Depending on the type of system you're running TinkerPilot on, here are the minimum requirements:

* macOS
    * Apple Silicon (M1+) — 8 GB RAM min.
    * Homebrew - Install script needs this to install missing dependencies if any.
    * Python 3.10 – 3.12 - Due to Kokora (TTS) and Moonshine Voice (STT) dependencies. Node.js 18+
    * [Ollama](https://ollama.com/), a tool to run LLMs locally. 
* Linux
    * x86_64 — 8 GB RAM min; NVIDIA GPU optional (CUDA auto-detected)
    * Python 3.10 – 3.12 and Node.js 18+
    * [Ollama](https://ollama.com/), a tool to run LLMs locally. 

## Quick setup

To setup TinkerPilot on your system, run this single command in your terminal:

```bash
curl -fsSL https://raw.githubusercontent.com/sudhanshu456/tinkerpilot/main/install.sh | bash
```

The installer automatically:
- Installs system dependencies.
- Downloads Ollama and the AI models, if not already installed and downloads the models if not already downloaded
- Interactively configures your preferences
  * HuggingFace Token, if you have one
  * Obsidian Vault path, if you have one
  * Enable Apple Notes integration, if you're running on macOS, want TinkerPilot to read your Apple notes for daily digest.
- Builds the UI into a static web app
- Creates a global `tp` command so you can use TinkerPilot from anywhere

**Note:** In any case the installer fails or you face any issues, first rerun the installer script. It should resolve most of the issues.

Once installed, simply run:

```bash
tp serve
```
This will start the AI backend and serve the Web UI at **http://localhost:8000**, or you can start using the CLI commands directly, see [Command Line Interface (CLI)](#command-line-interface-cli) section.

Below is the list of models used by TinkerPilot, you can change them later from the config file. See [Configuration](#configuration) section.

| Model | Purpose | Engine |
|-------|---------|--------|
| [Qwen2.5-3B-Instruct](https://huggingface.co/Qwen/Qwen2.5-3B-Instruct) | Chat, summarization, code analysis | Ollama |
| [Qwen3-Embedding 0.6B](https://huggingface.co/Qwen) | Text embeddings for RAG | Ollama |
| [Moonshine Voice](https://github.com/moonshine-ai/moonshine) | Speech-to-text (streaming) | Moonshine (ONNX) |
| [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) | Text-to-speech (6 voices) | PyTorch |


## Configuration

Tinkerpilot creates a config yaml under path `~/.tinkerpilot/config.yaml`, and you can edit it to change the default models, integrations, etc.

You can create this configuration file manually, before installing tinkerpilot, installer script will pick it up and use it.

> **Note on Model Configurability:**
> * **LLM & Embeddings**: Fully modular via Ollama. You can seamlessly switch to any model available on Ollama (e.g., `llama3.2`, `nomic-embed-text`).
> * **STT (Moonshine)**: The underlying engine is fixed, but you can configure the memory footprint via `model_size` (`tiny`, `small`, `medium`).
> * **TTS (Kokoro-82M)**: The underlying engine is fixed, but you can configure properties like `voice`, `speed`, and `lang_code`.

```yaml
hf_token: "hf_your_token_here..."  # Set this to disable unauthenticated HF warnings

llm:
  model_name: "qwen2.5:3b"  # any model from: ollama list
  temperature: 0.7

embedding:
  model_name: "qwen3-embedding:0.6b"  # or nomic-embed-text, mxbai-embed-large

stt:
  model_size: small  # tiny, small, medium
  language: en

tts:
  voice: "af_heart"  # Kokoro voice (e.g., af_heart, am_adam, af_bella)
  speed: 1.0
  lang_code: "a"     # a=American English, b=British

rag:
  chunk_size: 512
  top_k: 5

integrations:
  obsidian_vault_path: ~/Documents/ObsidianVault
  enable_apple_notes: true
```

## Command Line Interface (CLI)

TinkerPilot provides a powerful CLI to interact with its features directly from the terminal.

Installer script installs TinkerPilot `tp` cli globally, so you can use it from any folder/terminal.

### Common Commands

```bash
# Chat / RAG
tp ask "how does the auth module work?"
tp ask "explain the database schema" --no-rag

# Ingest documents
tp ingest ~/my-project
tp ingest ./report.pdf --tag "finance"

# Search
tp search "database migration"
tp search "database migration" --tag "finance"
tp search "database migration" --folder ~/my-project

# Meeting transcription
tp transcribe meeting-recording.wav

# Tasks
tp tasks
tp add-task "Fix auth bug" --priority high
tp done 3

# Code explanation
tp explain deploy.sh

# File conversion
tp convert data.csv --to json

# Shell command helper
tp cmd "find all python files modified in the last week"
tp cmd --voice  # Use voice-to-command instead of typing

# Git digest & Auto-commit messages
tp git-digest /path/to/repo
tp git-commit-msg .

# Text-to-speech
tp speak "Hello from TinkerPilot"
tp speak "Save this" --output speech.wav --voice adam
tp speak README.md --summarize
tp speak README.md --summarize --output summary.wav --voice michael
tp voices

# Check Git repo for leaked API keys/secrets
tp check-secrets .

# Daily digest
tp digest
```

For more information on CLI commands, see [CLI Reference](./references/cli-reference.md)

### Uninstall

If you ever want to completely remove TinkerPilot, its models, and its data, run:

```bash
curl -fsSL https://raw.githubusercontent.com/sudhanshu456/tinkerpilot/main/uninstall.sh | bash
```