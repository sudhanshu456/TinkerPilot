---
sidebar_position: 6
title: CLI Reference
---

# CLI Reference

TinkerPilot provides a powerful Command Line Interface (CLI) to interact with its features directly from your terminal.

If you have a global installation, use `tp` from any directory. If developing locally, you can use `cd backend && source .venv/bin/activate && python -m cli.main <cmd>`.

## General Features

### `ask`
Ask the local AI a question. By default, it will use your indexed local knowledge base (RAG).

**Examples:**
```bash
tp ask "how does the auth module work?"
```
*Ask without searching your documents:*
```bash
tp ask "explain the database schema" --no-rag
```

### `ingest`
Add documents or entire directories to your local knowledge base.

**Examples:**
```bash
tp ingest ~/my-project
tp ingest ./report.pdf --tag "finance"
```

### `search`
Perform a unified semantic search across all your indexed documents, tasks, and meetings.

**Examples:**
```bash
tp search "database migration"
tp search "database migration" --tag "finance"
tp search "database migration" --folder ~/my-project
```

### `transcribe`
Transcribe audio files using local speech-to-text.

**Example:**
```bash
tp transcribe meeting-recording.wav
```

### `digest`
Generate your customized daily digest, combining pending tasks, recent meeting summaries, and notes.

**Example:**
```bash
tp digest
```

## Task Management

### `tasks`
List all your active tasks.

**Example:**
```bash
tp tasks
```

### `add-task`
Create a new task in the Kanban board.

**Example:**
```bash
tp add-task "Fix auth bug" --priority high
```

### `done`
Mark a specific task as completed based on its ID.

**Example:**
```bash
tp done 3
```

## Developer Utilities

### `explain`
Get a clear, concise breakdown of how a script or code file works.

**Example:**
```bash
tp explain deploy.sh
```

### `convert`
Instantly convert files between different formats (e.g., CSV to JSON, image to PDF).

**Example:**
```bash
tp convert data.csv --to json
```

### `cmd`
Describe what you want to do in natural language, and TinkerPilot will give you the exact shell command to execute.

**Example:**
```bash
tp cmd "find all python files modified in the last week"
```

### `git-digest`
Generate a readable summary of recent git commit activity in a specific repository.

**Example:**
```bash
tp git-digest /path/to/repo
```

### `git-commit-msg`
Automatically generate conventional git commit messages based on your currently staged code diffs.

**Example:**
```bash
tp git-commit-msg .
```

### `check-secrets`
Scan your local directories for leaked API keys, tokens, and passwords before pushing to GitHub.

**Example:**
```bash
tp check-secrets .
```

## Text-to-Speech

### `speak`
Convert text or files into natural-sounding speech.

**Examples:**
```bash
tp speak "Hello from TinkerPilot"
tp speak "Save this to a file" --output speech.wav --voice adam
```
*Summarize a file and read it out loud:*
```bash
tp speak README.md --summarize --output summary.wav --voice michael
```

### `voices`
List all the available text-to-speech voices you can use.

**Example:**
```bash
tp voices
```

## Server Operations

### `serve`
Start the TinkerPilot AI backend server and serve the Web UI at **http://localhost:8000**.

**Example:**
```bash
tp serve
```