---
sidebar_position: 6
title: CLI Reference
---
TinkerPilot provides a powerful Command Line Interface (CLI) to interact with its features directly from your terminal.

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
Describe what you want to do in natural language or use your voice, and TinkerPilot will give you the exact shell command to execute.

**Examples:**
```bash
tp cmd "find all python files modified in the last week"
```
*Use voice-to-command instead of typing:*
```bash
tp cmd --voice
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

### `serve start`
Start the TinkerPilot AI backend and serve the Web UI at **http://localhost:8000**.

**Examples:**
```bash
# Start in foreground (default — shows logs in terminal)
tp serve start

# Start in background (returns immediately)
tp serve start -b

# Start in background with a specific log level
tp serve start -b --log-level debug

# Start in foreground but force console output (used internally)
tp serve start --console --log-level info
```

**Options:**

| Flag | Default | Description |
|------|---------|-------------|
| `--host`, `-h` | `127.0.0.1` | Host to bind to |
| `--port`, `-p` | `8000` | Port to bind to |
| `--background`, `-b` | `false` | Run in background; returns immediately |
| `--log-level` | `info` | Logging verbosity: `debug`, `info`, `warning`, `error` |
| `--no-open` | `false` | Don't auto-open browser on start |

### `serve stop`
Stop **all** running TinkerPilot server instances (both tracked and stray).

```bash
tp serve stop
```

### `serve` (shorthand)
Running `tp serve` without a subcommand is equivalent to `tp serve start` in foreground mode.

```bash
tp serve
```