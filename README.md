# TinkerPilot
Your truly local AI assitant, to be used for coding assistance, summarization, meeting transcription, task management, and developer utilities. 

TinkerPilot combines chat-with-docs, meeting transcription, task management, and developer utilities into a single local-first application powered by on-device AI inference. No cloud APIs. No data leaves your machine.

![Docs](https://img.shields.io/website?url=https%3A%2F%2Ftinkerpilot.onrender.com)

## Requirements

| | macOS | Linux |
|---|---|---|
| **Hardware** | Apple Silicon (M1+) — 8 GB RAM min, 16 GB+ recommended | x86_64 — 8 GB RAM min; NVIDIA GPU optional (CUDA auto-detected) |
| **OS tooling** | Homebrew | apt (Debian/Ubuntu) or yum (RHEL/Fedora) |
| **Python** | 3.10 – 3.12 | 3.10 – 3.12 |
| **Node.js** | 18+ | 18+ |
| **Disk** | ~3 GB for AI models | ~3 GB (CPU-only PyTorch) or ~5 GB (CUDA PyTorch) |

## AI Models

| Model | Purpose | Size | Engine |
|-------|---------|------|--------|
| Qwen2.5-3B-Instruct | Chat, summarization, code analysis | ~2.0 GB | Ollama |
| Qwen3-Embedding 0.6B | Text embeddings for RAG | ~639 MB | Ollama |
| Moonshine Voice | Speech-to-text (streaming) | ~250 MB | Moonshine (ONNX) |
| Kokoro-82M | Text-to-speech (6 voices) | ~82 MB | PyTorch |

## Quick Start (Global Installation)

The easiest way to install TinkerPilot as a standalone application is via the interactive installer.

Run this single command in your terminal:

```bash
curl -fsSL https://raw.githubusercontent.com/sudhanshu456/tinkerpilot/main/install.sh | bash
```

The installer automatically:
- Installs system dependencies (Homebrew, Python, Node, FFmpeg)
- Downloads Ollama and the AI models
- Interactively configures your preferences
  * HuggingFace Token, if you have one
  * Obsidian Vault path, if you have one
  * Enable Apple Notes integration, if you have one
- Builds the UI into a static web app
- Creates a global `tp` command so you can use TinkerPilot from anywhere

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

If you used the global installer, you can run `tp` from any folder. 
If developing locally, run `cd backend && source .venv/bin/activate && python -m cli.main <cmd>`.

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

# Start server
tp serve
```

## Configuration

Tinkerpilot creates a config yaml if you're installting from the installer script under path `~/.tinkerpilot/config.yaml`, 
and you can edit it to change the default models, integrations, etc.

You can create this configuration file manually, before installing tinkerpilot, installer script will pick it up and use it.

```yaml
hf_token: "hf_your_token_here..."  # Set this to disable unauthenticated HF warnings

llm:
  model_name: "qwen2.5:3b"  # any model from: ollama list
  temperature: 0.7

embedding:
  model_name: "qwen3-embedding:0.6b"  # or nomic-embed-text, mxbai-embed-large

stt:
  model_size: small  # tiny, base, small, medium, large
  language: en

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
