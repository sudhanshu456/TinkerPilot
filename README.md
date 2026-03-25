# TinkerPilot
Your truly local AI assitant, to be used for coding assistance, summarization, meeting transcription, task management, and developer utilities. It is lightweight and can be run on almost any local machine. For example, macbook air m1 with 8gb ram can run it smoothly.

All operations and features are powered by on-device AI inference. No cloud APIs. No data leaves your machine.

![Docs](https://img.shields.io/website?url=https%3A%2F%2Ftinkerpilot.onrender.com)

## Requirements

| | macOS | Linux |
|---|---|---|
| **Hardware** | Apple Silicon (M1+) — 8 GB RAM min, 16 GB+ recommended | x86_64 — 8 GB RAM min; NVIDIA GPU optional (CUDA auto-detected) |
| **OS tooling** | Homebrew | apt (Debian/Ubuntu) or yum (RHEL/Fedora) |
| **Python** | 3.10 – 3.12 | 3.10 – 3.12 |
| **Node.js** | 18+ | 18+ |
| **Disk** | ~3 GB for AI models | ~3 GB (CPU-only PyTorch) or ~5 GB (CUDA PyTorch) |

If you don't have GPU, it will run on CPU without much performance degradation.

Below is the list of models used by TinkerPilot, you can change them later from the config file. See [Configuration](#configuration) section.

## AI Models

| Model | Purpose | Engine |
|-------|---------|--------|
| [Qwen2.5-3B-Instruct](https://huggingface.co/Qwen/Qwen2.5-3B-Instruct) | Chat, summarization, code analysis | Ollama |
| [Qwen3-Embedding 0.6B](https://huggingface.co/Qwen) | Text embeddings for RAG | Ollama |
| [Moonshine Voice](https://github.com/moonshine-ai/moonshine) | Speech-to-text (streaming) | Moonshine (ONNX) |
| [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) | Text-to-speech (6 voices) | PyTorch |

## Quick Start

The easiest way to install TinkerPilot as a standalone application is via the interactive installer.

> **Before you run:** Ensure you have [Ollama](https://ollama.com/) installed on your system, and Homebrew installed if you are on macOS. If Ollama is not installed, the installer script will try to install it for you, but it is recommended to install it yourself beforehand.

Run this single command in your terminal:
```bash
curl -fsSL https://raw.githubusercontent.com/sudhanshu456/tinkerpilot/main/install.sh | bash
```

The installer automatically:
- Installs system dependencies (Homebrew, Python (recommended version 3.10-3.12), Node, FFmpeg)
- Downloads Ollama and the AI models, if not already installed and downloads the models if not already downloaded
- Interactively configures your preferences
  * HuggingFace Token, if you have one
  * Obsidian Vault path, if you have one
  * Enable Apple Notes integration, if you have one
- Builds the UI into a static web app
- Creates a global `tp` command so you can use TinkerPilot from anywhere

Note: In any case the installer fails or you face any issues, first rerun the installer script. It should resolve most of the issues. Otherwise, ensure you have Ollama installed in your system. You can install it from [here](https://ollama.com/). 

Once installed, simply run:

```bash
tp serve
```
This will start the AI backend and serve the Web UI at **http://localhost:8000**.


### Uninstall

If you ever want to completely remove TinkerPilot, its models, and its data, run:

```bash
curl -fsSL https://raw.githubusercontent.com/sudhanshu456/tinkerpilot/main/uninstall.sh | bash
```

## CLI Usage

Once installed, you can use TinkerPilot from anywhere by running `tp` command, for examples:

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

`tp` cli allow to spin up the web interface only when it is required. 

To spin up the web interface, run:

```bash
tp serve
```

This will spin up the web interface at **http://localhost:8000**, and you can use it to interact with TinkerPilot, to look at the meetings, tasks, search, ingest documents, etc. 

## Configuration

Tinkerpilot creates a config yaml if you're installting from the installer script under path `~/.tinkerpilot/config.yaml`, 
and you can edit it to change the default models, integrations, etc.

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

## Privacy & Security

- All AI inference runs locally on your hardware (via Ollama)
- No data is sent to any cloud service
- All data stored in `~/.tinkerpilot/` on your local filesystem
- Apple Notes access requires explicit macOS permission grants
- No telemetry, no analytics, no tracking

## License

MIT
