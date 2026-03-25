---
sidebar_position: 1
title: TinkerPilot
---
TinkerPilot combines chat-with-docs, meeting transcription, task management, and developer utilities into a single local-first application powered by on-device AI inference. No cloud APIs. No data leaves your machine.

## Features
### Developer Utilities

| Feature                | CLI / UI Reference | Description                                                                                         |
| ---------------------- | ------------------ | --------------------------------------------------------------------------------------------------- |
| **Code Explainer**     | [`tp explain`](./cli-reference.md#explain) | Drop in any confusing script or code file and get a clear, concise breakdown of how it works.         |
| **Log Analyzer**       | Web UI / `tp ask`  | Paste messy error logs to instantly get error patterns and actionable suggested fixes.                |
| **Command Helper**     | [`tp cmd`](./cli-reference.md#cmd) | Describe what you want to do (via typing or **voice-to-command**) to get the exact shell command to execute. |
| **Git Commit Generator**| [`tp git-commit-msg`](./cli-reference.md#git-commit-msg) | Auto-generate conventional git commit messages based on your staged code diffs.                      |
| **Git Digest**         | [`tp git-digest`](./cli-reference.md#git-digest) | Summarize recent git commit activity in any repository into a readable report.                      |
| **Secret Scanner**     | [`tp check-secrets`](./cli-reference.md#check-secrets) | Scan local directories for leaked API keys, tokens, and passwords before pushing to GitHub.           |
| **File Conversions**   | [`tp convert`](./cli-reference.md#convert) | Instantly convert files: CSV ↔ JSON, images ➡️ PDF, base64 encode/decode.                         |

### Meetings & Audio

| Feature                   | CLI / UI Reference | Description                                                                                         |
| ------------------------- | ------------------ | --------------------------------------------------------------------------------------------------- |
| **Meeting Transcription** | [`tp transcribe`](./cli-reference.md#transcribe) | Record live or upload audio. Get precise transcripts + structured summaries.                        |
| **Action Item Extraction**| Auto via [`tp transcribe`](./cli-reference.md#transcribe) | Automatically pulls action items from meeting summaries and creates tasks.                           |
| **Text-to-Speech**        | [`tp speak`](./cli-reference.md#speak) | Convert text into incredibly natural-sounding speech with multiple distinct voices.                   |

### Local Knowledge

| Feature                 | CLI / UI Reference | Description                                                                                         |
| ----------------------- | ------------------ | --------------------------------------------------------------------------------------------------- |
| **Chat with Documents** | [`tp ask`](./cli-reference.md#ask) / [`tp ingest`](./cli-reference.md#ingest) | Ingest PDFs, code, markdown, CSV, JSON. Ask questions with RAG-powered semantic search and precise source citations. |
| **Unified Search**      | [`tp search`](./cli-reference.md#search) | Search across all your documents, tasks, meetings, and notes from a single interface.              |
| **Obsidian Integration**| Web UI / [`tp search`](./cli-reference.md#search) | Index and search your entire Obsidian markdown vault using semantic AI search.                     |
| **Apple Notes Sync**    | Web UI / [`tp search`](./cli-reference.md#search) | Automatically search and retrieve notes directly from your macOS Notes app.                         |

### Task Manager & Follow-ups

| Feature           | CLI / UI Reference | Description                                                                                         |
| ----------------- | ------------------ | --------------------------------------------------------------------------------------------------- |
| **Daily Digest**  | [`tp digest`](./cli-reference.md#digest) | A custom morning/evening briefing combining pending tasks, recent meeting summaries, and notes.       |
| **Task Manager**  | [`tp tasks`](./cli-reference.md#tasks) | Create, track, and complete tasks. Kanban-style web UI for managing action items.                   |

## Privacy & Security

-   All AI inference runs locally on your hardware (via Ollama)
-   No data is sent to any cloud service
-   All data stored in `~/.tinkerpilot/` on your local filesystem
-   Apple Notes access requires explicit macOS permission grants
-   No telemetry, no analytics, no tracking

For a detailed look at the architecture, see the [Architecture Overview](./architecture.md).
