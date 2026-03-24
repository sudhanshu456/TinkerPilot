# TinkerPilot

**Local AI assistant for developers. Privacy-first, offline, runs entirely on your machine.**

TinkerPilot combines chat-with-docs, meeting transcription, task management, and developer utilities into a single local-first application powered by on-device AI inference. No cloud APIs. No data leaves your machine.

## Features

| Feature | Description |
|---------|-------------|
| **Chat with Documents** | Ingest PDFs, code, markdown, CSV, JSON. Ask questions with RAG-powered semantic search and source citations. |
| **Meeting Transcription** | Upload audio files, get transcripts + structured summaries with action items (auto-created as tasks). |
| **Speech-to-Text** | Record and transcribe speech from the terminal. |
| **Daily Digest** | Morning briefing combining pending tasks, recent meeting summaries, and notes. |
| **Task Manager** | Create, track, and complete tasks. Auto-extracted from meeting summaries. Kanban-style web UI. |
| **Apple Notes Search** | Search and retrieve notes from the macOS Notes app. |
| **Obsidian Integration** | Index and search your Obsidian vault with semantic search. |
| **Code Explainer** | Drop in any script or code file, get a clear explanation. |
| **Log Analyzer** | Paste logs, get error patterns and suggested fixes. |
| **Git Digest** | Summarize recent git activity in any repository. |
| **Command Helper** | Describe what you want in English, get a shell command. |
| **File Conversions** | CSV to JSON, JSON to CSV, image to PDF, base64 encode/decode. |
| **Unified Search** | Search across documents, tasks, meetings, and notes from one place. |

## Architecture

```
Web UI (Next.js :3000) + CLI (`tp`)
         │
    FastAPI Backend (:8000)
         │
    ┌────┴────────────────────┐
    │    Ollama (:11434)      │
    │  Qwen2.5-3B (Metal GPU) │  ← Chat, summarization
    │  Qwen3-Embed-0.6B       │  ← Embeddings for RAG
    └────┬────────────────────┘
         │
    ┌────┴────────────────────┐
    │    Moonshine Voice       │  ← Speech-to-text
    │    Kokoro-82M            │  ← Text-to-speech
    │    ChromaDB (vectors)    │
    │    SQLite (structured)   │
    └─────────────────────────┘
```

All inference runs locally via Ollama with Apple Metal GPU acceleration. See [docs/MODEL_SELECTION.md](docs/MODEL_SELECTION.md) for detailed model justification.

## Requirements

- **macOS** with Apple Silicon (M1/M2/M3/M4) — 8GB RAM minimum
- **Homebrew** (package manager)
- **Python 3.10+**
- **Node.js 18+**
- ~3 GB disk space for models

## Quick Start (Global Installation)

The easiest way to install TinkerPilot as a standalone macOS application is via the interactive installer.

Run this single command in your terminal:

```bash
curl -fsSL https://raw.githubusercontent.com/sudhanshu/tinkerpilot/main/install.sh | bash
```

The installer automatically:
- Installs system dependencies (Homebrew, Python, Node, FFmpeg)
- Downloads Ollama and the AI models
- Interactively configures your preferences
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
curl -fsSL https://raw.githubusercontent.com/sudhanshu/tinkerpilot/main/uninstall.sh | bash
```

## Local Development

If you want to edit the code or run TinkerPilot in development mode (with hot-reloading Next.js):

### 1. Setup (one time)

```bash
git clone <repo-url> TinkerPilot
cd TinkerPilot
./scripts/setup.sh
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

## CLI Usage

If you used the global installer, you can run `tp` from any folder. 
If developing locally, run `cd backend && source .venv/bin/activate && python -m cli.main <cmd>`.

```bash
# Chat / RAG
tp ask "how does the auth module work?"
tp ask "explain the database schema" --no-rag

# Ingest documents
tp ingest ~/my-project
tp ingest ./report.pdf

# Search
tp search "database migration"

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

# Git digest & Auto-commit messages
tp git-digest /path/to/repo
tp git-commit-msg .

# Text-to-speech
tp speak "Hello from TinkerPilot"
tp speak "Save this" --output speech.wav --voice adam
tp voices

# Check Git repo for leaked API keys/secrets
tp check-secrets .

# Daily digest
tp digest

# Start server
tp serve
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/chat` | Send a chat message (with/without RAG) |
| WS | `/api/ws/chat` | WebSocket streaming chat |
| GET | `/api/chat/history` | Get chat history |
| POST | `/api/documents/upload` | Upload and ingest a file |
| POST | `/api/documents/ingest` | Ingest a local path |
| GET | `/api/documents` | List indexed documents |
| POST | `/api/meetings/transcribe` | Upload audio and transcribe |
| GET | `/api/meetings` | List meetings |
| POST/GET/PUT/DELETE | `/api/tasks` | Task CRUD |
| GET | `/api/digest` | Generate daily digest |
| GET/POST | `/api/search` | Unified search |
| POST | `/api/utils/explain` | Explain code |
| POST | `/api/utils/cmd` | Natural language to shell command |
| POST | `/api/utils/git-digest` | Summarize git activity |
| POST | `/api/utils/speak` | Text-to-speech (returns WAV) |
| GET | `/api/utils/voices` | List available TTS voices |

## AI Models

| Model | Purpose | Size | Engine |
|-------|---------|------|--------|
| Qwen2.5-3B-Instruct | Chat, summarization, code analysis | ~2.0 GB | Ollama (Metal GPU) |
| Qwen3-Embedding 0.6B | Text embeddings for RAG | ~639 MB | Ollama (Metal GPU) |
| Moonshine Voice | Speech-to-text (streaming) | ~250 MB | Moonshine (ONNX) |
| Kokoro-82M | Text-to-speech (6 voices) | ~82 MB | PyTorch (MPS GPU) |

See [docs/MODEL_SELECTION.md](docs/MODEL_SELECTION.md) for detailed rationale and alternatives analysis.

## Configuration

Create `~/.tinkerpilot/config.yaml` to customize:

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
