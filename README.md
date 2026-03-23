# TinkerPilot

**Local AI assistant for developers. Privacy-first, offline, runs entirely on your machine.**

TinkerPilot combines chat-with-docs, meeting transcription, task management, calendar sync, and developer utilities into a single local-first application powered by on-device AI inference. No cloud APIs. No data leaves your machine.

## Features

| Feature | Description |
|---------|-------------|
| **Chat with Documents** | Ingest PDFs, code, markdown, CSV, JSON. Ask questions with RAG-powered semantic search and source citations. |
| **Meeting Transcription** | Upload audio files, get transcripts + structured summaries with action items (auto-created as tasks). |
| **Speech-to-Text** | Record and transcribe speech from the terminal. |
| **Daily Digest** | Morning briefing combining calendar events, pending tasks, and recent meeting summaries. |
| **Task Manager** | Create, track, and complete tasks. Auto-extracted from meeting summaries. Kanban-style web UI. |
| **Apple Calendar Sync** | Reads today's events from macOS Calendar app. |
| **Apple Notes Search** | Search and retrieve notes from the macOS Notes app. |
| **Obsidian Integration** | Index and search your Obsidian vault with semantic search. |
| **Code Explainer** | Drop in any script or code file, get a clear explanation. |
| **Log Analyzer** | Paste logs, get error patterns and suggested fixes. |
| **Git Digest** | Summarize recent git activity in any repository. |
| **Command Helper** | Describe what you want in English, get a shell command. |
| **File Conversions** | CSV to JSON, JSON to CSV, image to PDF, base64 encode/decode. |
| **Unified Search** | Search across documents, tasks, meetings, and notes from one place. |
| **Test Checklist** | Generate QA checklists from code. |
| **Repro Steps** | Suggest bug reproduction steps from descriptions or logs. |

## Architecture

```
Web UI (Next.js :3000) + CLI (`tp`)
         │
    FastAPI Backend (:8000)
         │
    ┌────┴────────────────────┐
    │      AI Inference       │
    │  llama-cpp-python       │  ← Qwen2.5-3B (Metal GPU)
    │  faster-whisper         │  ← Whisper small (int8)
    │  nomic-embed (via llama)│  ← 768-dim embeddings
    └────┬────────────────────┘
         │
    ┌────┴────────────────────┐
    │      Data Layer         │
    │  ChromaDB (vectors)     │
    │  SQLite (structured)    │
    │  File system (docs)     │
    └─────────────────────────┘
```

All inference runs locally via Apple Metal GPU acceleration. See [docs/MODEL_SELECTION.md](docs/MODEL_SELECTION.md) for detailed model justification.

## Requirements

- **macOS** with Apple Silicon (M1/M2/M3/M4) — 8GB RAM minimum
- **Python 3.10+**
- **Node.js 18+**
- ~3 GB disk space for models

## Quick Start

### 1. Clone and setup

```bash
git clone <repo-url> TinkerPilot
cd TinkerPilot
chmod +x scripts/setup.sh
./scripts/setup.sh
```

The setup script will:
- Create a Python virtual environment
- Install llama-cpp-python with Metal GPU support
- Install all Python and Node.js dependencies
- Download AI models (~2.1 GB)
- Initialize the database

### 2. Start the backend

```bash
cd backend
source .venv/bin/activate
python -m cli.main serve
```

### 3. Start the frontend

```bash
cd frontend
npm run dev
```

### 4. Open http://localhost:3000

## Manual Setup (if setup.sh fails)

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate

# Install llama-cpp-python with Metal
CMAKE_ARGS="-DGGML_METAL=on" pip install llama-cpp-python --no-cache-dir

# Install dependencies
pip install -e .

# Download models
python ../scripts/download_models.py

# Start server
python -m cli.main serve
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## CLI Usage

All CLI commands are available via `python -m cli.main` (from the `backend/` directory with venv activated):

```bash
# Chat / RAG
python -m cli.main ask "how does the auth module work?"
python -m cli.main ask "explain the database schema" --no-rag

# Ingest documents
python -m cli.main ingest ~/my-project
python -m cli.main ingest ./report.pdf

# Search
python -m cli.main search "database migration"

# Meeting transcription
python -m cli.main transcribe meeting-recording.wav
python -m cli.main transcribe call.mp3 --no-summarize

# Tasks
python -m cli.main tasks
python -m cli.main add-task "Fix auth bug" --priority high
python -m cli.main done 3

# Code explanation
python -m cli.main explain deploy.sh
python -m cli.main explain main.py --question "what does the retry logic do?"

# File conversion
python -m cli.main convert data.csv --to json
python -m cli.main convert users.json --to csv
python -m cli.main convert screenshot.png --to pdf

# Shell command helper
python -m cli.main cmd "find all python files modified in the last week"
python -m cli.main cmd "compress all logs older than 30 days"

# Git digest
python -m cli.main git-digest /path/to/repo
python -m cli.main git-digest . --commits 50

# Speech-to-text
python -m cli.main listen --duration 15

# Daily digest
python -m cli.main digest

# Start server
python -m cli.main serve --port 8000
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/chat` | Send a chat message (with/without RAG) |
| WS | `/ws/chat` | WebSocket streaming chat |
| GET | `/api/chat/history` | Get chat history |
| POST | `/api/documents/upload` | Upload and ingest a file |
| POST | `/api/documents/ingest` | Ingest a local path |
| GET | `/api/documents` | List indexed documents |
| DELETE | `/api/documents/{id}` | Remove a document |
| POST | `/api/meetings/transcribe` | Upload audio and transcribe |
| POST | `/api/meetings/summarize` | Summarize a transcript |
| GET | `/api/meetings` | List meetings |
| GET | `/api/meetings/{id}` | Get meeting detail |
| POST/GET/PUT/DELETE | `/api/tasks` | Task CRUD |
| GET | `/api/digest` | Generate daily digest |
| GET/POST | `/api/search` | Unified search |
| POST | `/api/utils/explain` | Explain code |
| POST | `/api/utils/analyze-log` | Analyze log files |
| POST | `/api/utils/cmd` | Natural language to shell command |
| POST | `/api/utils/git-digest` | Summarize git activity |
| POST | `/api/utils/convert/*` | File conversions |
| POST | `/api/utils/test-checklist` | Generate test checklist |
| POST | `/api/utils/repro-steps` | Suggest bug repro steps |

## AI Models

| Model | Purpose | Size | Engine |
|-------|---------|------|--------|
| Qwen2.5-3B-Instruct (Q4_K_M) | Chat, summarization, code analysis | 2.0 GB | llama-cpp-python + Metal |
| nomic-embed-text-v1.5 (Q4_K_M) | Text embeddings for RAG | 78 MB | llama-cpp-python |
| Whisper small (int8) | Speech-to-text | 500 MB | faster-whisper (CTranslate2) |

See [docs/MODEL_SELECTION.md](docs/MODEL_SELECTION.md) for detailed rationale, benchmarks, and alternatives analysis.

## Configuration

Create `~/.tinkerpilot/config.yaml` to customize:

```yaml
llm:
  model_path: /path/to/custom-model.gguf
  n_ctx: 4096
  n_gpu_layers: -1
  temperature: 0.7

embedding:
  model_path: /path/to/embedding-model.gguf

whisper:
  model_size: small  # tiny, base, small, medium, large
  language: en

rag:
  chunk_size: 512
  chunk_overlap: 50
  top_k: 5

integrations:
  obsidian_vault_path: ~/Documents/ObsidianVault
  enable_apple_calendar: true
  enable_apple_notes: true
```

## Project Structure

```
TinkerPilot/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── config.py            # Configuration management
│   │   ├── api/                 # REST API endpoints
│   │   │   ├── chat.py          # Chat + WebSocket streaming
│   │   │   ├── documents.py     # Document ingestion
│   │   │   ├── meetings.py      # Meeting transcription
│   │   │   ├── tasks.py         # Task management
│   │   │   ├── digest.py        # Daily digest
│   │   │   ├── search.py        # Unified search
│   │   │   └── utils.py         # Dev utilities
│   │   ├── core/                # AI and processing
│   │   │   ├── llm.py           # LLM wrapper (llama-cpp-python)
│   │   │   ├── embeddings.py    # Embedding wrapper
│   │   │   ├── whisper_stt.py   # Speech-to-text wrapper
│   │   │   ├── rag.py           # RAG pipeline
│   │   │   ├── parsers.py       # File format parsers
│   │   │   └── chunker.py       # Text chunking
│   │   ├── integrations/        # External integrations
│   │   │   ├── apple_calendar.py
│   │   │   ├── apple_notes.py
│   │   │   └── obsidian.py
│   │   └── db/                  # Data layer
│   │       ├── models.py        # SQLModel schemas
│   │       ├── sqlite.py        # SQLite setup
│   │       └── vector.py        # ChromaDB setup
│   ├── cli/
│   │   └── main.py              # CLI (`tp` command)
│   └── pyproject.toml
├── frontend/                    # Next.js web UI
│   └── src/app/
│       ├── page.tsx             # Dashboard / Daily Digest
│       ├── chat/page.tsx        # Chat with documents
│       ├── meetings/page.tsx    # Meeting management
│       ├── tasks/page.tsx       # Task board
│       ├── search/page.tsx      # Unified search
│       └── settings/page.tsx    # Settings + document management
├── scripts/
│   ├── setup.sh                 # One-command setup
│   └── download_models.py       # Model downloader
├── docs/
│   └── MODEL_SELECTION.md       # Model justification document
├── models/                      # Downloaded GGUF models
└── data/                        # Runtime data
```

## Privacy & Security

- All AI inference runs locally on your hardware
- No data is sent to any cloud service
- All data stored in `~/.tinkerpilot/` on your local filesystem
- Apple Calendar/Notes access requires explicit macOS permission grants
- No telemetry, no analytics, no tracking

## Supported File Types

Documents: `.pdf`, `.md`, `.txt`, `.rst`, `.docx`
Code: `.py`, `.js`, `.ts`, `.tsx`, `.jsx`, `.java`, `.go`, `.rs`, `.c`, `.cpp`, `.rb`, `.php`, `.swift`, `.sh`, `.sql`, and more
Data: `.csv`, `.json`, `.jsonl`, `.xml`, `.html`
Config: `.yaml`, `.yml`, `.toml`, `.ini`, `.env`
Logs: `.log`

## License

MIT
