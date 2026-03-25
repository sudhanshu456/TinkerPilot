---
sidebar_position: 1
title: Backend
---
The TinkerPilot backend is a Python application built with [FastAPI](https://fastapi.tiangolo.com/). It serves as the core engine for the entire application, handling API requests, AI inference, database operations, and serving the frontend in a production environment.

## API Server

The main entry point for the backend is `backend/app/main.py`. This file initializes the FastAPI application, sets up middleware, and includes all the API routers.

### Lifespan Management

The `@asynccontextmanager lifespan` function in `main.py` handles startup and shutdown logic. On startup, it:
-   Ensures all necessary directories exist.
-   Initializes the SQLite database.
-   Handles background tasks like indexing an Obsidian vault (if configured) and pre-warming the daily digest.

### CORS Middleware

The backend is configured with CORS (Cross-Origin Resource Sharing) to allow the frontend development server (running on `localhost:3000`) to communicate with the API server (running on `localhost:8000`).

### Serving the Frontend

In a production build (created via the global installer), the FastAPI server is also responsible for serving the static Next.js frontend. The `serve_frontend` function in `main.py` handles this, allowing TinkerPilot to run as a single, self-contained application.

## API Endpoints

The API is organized into several routers, each corresponding to a specific feature. The main routers are:

| Router          | Prefix         | Description                                     |
| --------------- | -------------- | ----------------------------------------------- |
| `chat_router`   | `/api`         | Handles chat messages and WebSocket connections |
| `documents_router`| `/api`         | Manages document ingestion and retrieval        |
| `meetings_router` | `/api`         | Handles meeting transcription and summaries     |
| `tasks_router`  | `/api`         | Provides CRUD operations for tasks              |
| `digest_router` | `/api`         | Generates the daily digest                      |
| `search_router` | `/api`         | Powers the unified search                       |
| `utils_router`  | `/api`         | Provides various developer utilities            |

Here is a list of the most important endpoints:

| Method | Endpoint                  | Description                        |
| ------ | ------------------------- | ---------------------------------- |
| GET    | `/api/health`             | Health check                       |
| POST   | `/api/chat`               | Send a chat message (with/without RAG) |
| WS     | `/api/ws/chat`            | WebSocket streaming chat           |
| GET    | `/api/chat/history`       | Get chat history                   |
| POST   | `/api/documents/upload`   | Upload and ingest a file           |
| POST   | `/api/documents/ingest`   | Ingest a local path                |
| GET    | `/api/documents`          | List indexed documents             |
| POST   | `/api/meetings/transcribe`| Upload audio and transcribe        |
| GET    | `/api/meetings`           | List meetings                      |
| POST/GET/PUT/DELETE | `/api/tasks` | Task CRUD                          |
| GET    | `/api/digest`             | Generate daily digest              |
| GET/POST | `/api/search`           | Unified search                     |
| POST   | `/api/utils/explain`      | Explain code                       |
| POST   | `/api/utils/cmd`          | Natural language to shell command  |
| POST   | `/api/utils/git-digest`   | Summarize git activity             |
| POST   | `/api/utils/speak`        | Text-to-speech (returns WAV)       |
| GET    | `/api/utils/voices`       | List available TTS voices          |

## Database

TinkerPilot uses SQLite for storing structured data. The database models are defined in `backend/app/db/models.py` using [SQLModel](https://sqlmodel.tiangolo.com/).

### Database Schema

There are four main tables in the database:

-   **`Document`**: Tracks ingested documents for RAG. It stores metadata like the filename, path, file type, and the number of chunks.
-   **`Meeting`**: Stores meeting transcriptions and summaries, along with metadata like the date, duration, and the path to the audio file.
-   **`Task`**: Represents a single task or to-do item. Tasks can be linked to a source, such as a meeting or a document.
-   **`ChatMessage`**: Stores the chat history for all conversations. Each message has a role (`user` or `assistant`) and content.

This simple but effective schema allows TinkerPilot to store and manage all the user's data locally.
