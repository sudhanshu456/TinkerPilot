---
sidebar_position: 2
title: Running the App
---

# Running the App

This guide explains how to run TinkerPilot in different modes and how to use the Command Line Interface (CLI).

## Running in Production Mode (Global Install)

If you have installed TinkerPilot globally using the installer, you can run it from any directory using the `tp` command.

To start the server, run:

```bash
tp serve
```

This will start the AI backend and serve the Web UI at **http://localhost:8000**.

## Running in Development Mode

If you have set up a local development environment, you can run the application with hot-reloading for both the frontend and backend.

Use the `start.sh` script to launch all the required services:

```bash
./scripts/start.sh
```

This script will:
1.  Start the Ollama server.
2.  Start the Python FastAPI backend.
3.  Start the Next.js development server.

You can access the web interface at **http://localhost:3000**.

Alternatively, you can use the `Makefile`:

```bash
make run
```

## Command Line Interface (CLI)

TinkerPilot provides a powerful CLI to interact with its features directly from the terminal.

If you have a global installation, you can use `tp` from any folder. If you are in a local development environment, you need to activate the virtual environment first: `cd backend && source .venv/bin/activate && python -m cli.main <cmd>`.

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
