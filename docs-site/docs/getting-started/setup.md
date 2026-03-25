---
sidebar_position: 1
title: Setup Instructions
---

# Setup Instructions

This guide will walk you through setting up TinkerPilot on your local machine.

## Requirements

|                 | macOS                                                       | Linux                                                              |
| --------------- | ----------------------------------------------------------- | ------------------------------------------------------------------ |
| **Hardware**    | Apple Silicon (M1+) — 8 GB RAM min, 16 GB+ recommended      | x86_64 — 8 GB RAM min; NVIDIA GPU optional (CUDA auto-detected)    |
| **OS tooling**  | Homebrew                                                    | apt (Debian/Ubuntu) or yum (RHEL/Fedora)                           |
| **Python**      | 3.10 – 3.12                                                 | 3.10 – 3.12                                                        |
| **Node.js**     | 18+                                                         | 18+                                                                |
| **Disk**        | ~3 GB for AI models                                         | ~3 GB (CPU-only PyTorch) or ~5 GB (CUDA PyTorch)                   |

### Python Dependencies (installed automatically)

| Package                 | Purpose                               |
| ----------------------- | ------------------------------------- |
| `fastapi`, `uvicorn`    | Backend API server                    |
| `moonshine-voice`       | Speech-to-text (pulls PyTorch)        |
| `kokoro`                | Text-to-speech (pulls PyTorch)        |
| `chromadb`              | Vector database for RAG               |
| `sqlmodel`, `aiosqlite` | SQLite ORM + async driver             |
| `PyMuPDF`, `python-docx`| PDF and DOCX parsing                  |
| `sounddevice`, `soundfile`| Audio I/O                             |
| `typer`, `rich`         | CLI framework                         |
| `httpx`                 | HTTP client (Ollama communication)    |
| `pyyaml`                | Config file parsing                   |
| `img2pdf`               | Image-to-PDF conversion               |

> **Note:** The installer pre-installs only the minimal ML runtime needed for your platform — just `torch` (for TTS) and `onnxruntime` (for STT). Unnecessary transitive dependencies like `torchaudio`, `torchvision`, and `onnxruntime-gpu` are avoided. On Linux without an NVIDIA GPU, CPU-only PyTorch (~1 GB) is used instead of the default CUDA build (~2.5 GB).

## Quick Start (Global Installation)

The easiest way to install TinkerPilot as a standalone application is via the interactive installer.

Run this single command in your terminal:

```bash
curl -fsSL https://raw.githubusercontent.com/sudhanshu456/tinkerpilot/main/install.sh | bash
```

The installer automatically:
-   Installs system dependencies (Homebrew, Python, Node, FFmpeg)
-   Downloads Ollama and the AI models
-   Interactively configures your preferences
-   Builds the UI into a static web app
-   Creates a global `tp` command so you can use TinkerPilot from anywhere

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

## Local Development

If you want to edit the code or run TinkerPilot in development mode (with hot-reloading Next.js):

### 1. Setup (one time)

```bash
git clone <repo-url> TinkerPilot
cd TinkerPilot
./scripts/setup.sh      # macOS (uses Homebrew)
# Or on Linux, use the global installer which handles apt/yum:
# curl -fsSL https://raw.githubusercontent.com/sudhanshu456/tinkerpilot/main/install.sh | bash
```

### 2. Run (Development Mode)

```bash
./scripts/start.sh
```

This starts Ollama, the Python FastAPI backend, and the Next.js dev server. Open **http://localhost:3000**.

### 3. Or use Make

```bash
make setup   # one-time setup
make run     # start everything
```

## Manual Setup (if setup.sh fails)

```bash
# 1. Install Ollama
brew install ollama

# 2. Pull models
ollama pull qwen2.5:3b
ollama pull qwen3-embedding:0.6b

# 3. Python backend
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# 4. Frontend
cd ../frontend
npm install

# 5. Start (3 terminals)
ollama serve                              # Terminal 1
cd backend && source .venv/bin/activate && python -m cli.main serve  # Terminal 2
cd frontend && npm run dev                # Terminal 3

# Open http://localhost:3000
```
