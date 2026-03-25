---
sidebar_position: 1
title: App Overview
---

# TinkerPilot

**Local AI assistant for developers. Privacy-first, offline, runs entirely on your machine.**

TinkerPilot combines chat-with-docs, meeting transcription, task management, and developer utilities into a single local-first application powered by on-device AI inference. No cloud APIs. No data leaves your machine.

## Features

### Coding & Debug

| Feature                | Description                                                                                         |
| ---------------------- | --------------------------------------------------------------------------------------------------- |
| **Code Explainer**     | Drop in any confusing script or code file and get a clear, concise breakdown of how it works.         |
| **Log Analyzer**       | Paste messy error logs to instantly get error patterns and actionable suggested fixes.                |
| **Git Commit Generator**| Auto-generate conventional git commit messages based on your staged code diffs.                      |
| **Git Digest**         | Summarize recent git commit activity in any repository into a readable report.                      |
| **Secret Scanner**     | Scan local directories for leaked API keys, tokens, and passwords before pushing to GitHub.           |
| **Command Helper**     | Describe what you want to do in English, and get the exact shell command to execute.                |
| **File Conversions**   | Instantly convert files: CSV ↔ JSON, images ➡️ PDF, base64 encode/decode.                         |

### Meetings

| Feature                   | Description                                                                                         |
| ------------------------- | --------------------------------------------------------------------------------------------------- |
| **Meeting Transcription** | Record live or upload audio. Get precise transcripts + structured summaries.                        |
| **Action Item Extraction**| Automatically pulls action items from meeting summaries and creates tasks.                           |
| **Speech-to-Text**        | Record and transcribe your voice directly from the terminal.                                        |
| **Text-to-Speech**        | Convert text into incredibly natural-sounding speech with multiple distinct voices.                   |

### Local Knowledge

| Feature                 | Description                                                                                         |
| ----------------------- | --------------------------------------------------------------------------------------------------- |
| **Chat with Documents** | Ingest PDFs, code, markdown, CSV, JSON. Ask questions with RAG-powered semantic search and precise source citations. |
| **Unified Search**      | Search across all your documents, tasks, meetings, and notes from a single interface.              |
| **Obsidian Integration**| Index and search your entire Obsidian markdown vault using semantic AI search.                     |
| **Apple Notes Sync**    | Automatically search and retrieve notes directly from your macOS Notes app.                         |

### Task Manager & Follow ups

| Feature           | Description                                                                                         |
| ----------------- | --------------------------------------------------------------------------------------------------- |
| **Daily Digest**  | A custom morning/evening briefing combining pending tasks, recent meeting summaries, and notes.       |
| **Task Manager**  | Create, track, and complete tasks. Kanban-style web UI for managing action items.                   |

## Privacy & Security

-   All AI inference runs locally on your hardware (via Ollama)
-   No data is sent to any cloud service
-   All data stored in `~/.tinkerpilot/` on your local filesystem
-   Apple Notes access requires explicit macOS permission grants
-   No telemetry, no analytics, no tracking

For a detailed look at the architecture, see the [Architecture Overview](./architecture.md).
