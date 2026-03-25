---
sidebar_position: 2
title: Architecture
---
TinkerPilot is designed as a standalone, offline-first application. When installed globally, it runs as a single lightweight FastAPI server that mounts the static Next.js frontend, entirely eliminating the need for Node.js at runtime.

```mermaid
graph TD
    subgraph Interfaces [Interfaces]
        UI[Web UI<br/>React / Static Export]
        CLI[Terminal CLI<br/>'tp' command]
    end

    subgraph CoreEngine [Core Engine Port 8000]
        API[FastAPI Server]
    end

    subgraph AIInference [AI Inference]
        OLLAMA[Ollama Server<br/>Port 11434]
        LLM[Qwen2.5 3B<br/>Text Generation]
        EMB[Qwen3 0.6B<br/>Embeddings]
        STT[Moonshine Voice<br/>Speech-to-Text]
        TTS[Kokoro-82M<br/>Text-to-Speech]
    end

    subgraph LocalStorage [Local Storage ~/.tinkerpilot]
        SQL[(SQLite<br/>Tasks, Meetings)]
        VEC[(ChromaDB<br/>Document Vectors)]
        FILES[Audio & File Storage]
    end

    subgraph macOSIntegrations [macOS Integrations]
        NOTES[Apple Notes<br/>via AppleScript]
        OBS[Obsidian Vault<br/>via File Watcher]
    end

    UI <--> API
    CLI <--> API
    
    API <--> OLLAMA
    OLLAMA --> LLM
    OLLAMA --> EMB
    API --> STT
    API --> TTS
    
    API <--> SQL
    API <--> VEC
    API <--> FILES
    API <--> NOTES
    API <--> OBS
```

### Technical Stack & Decisions

*   **Frontend:** Next.js (React) configured for `output: export`. Compiles to static HTML/JS for zero-dependency hosting.
*   **Backend:** Python FastAPI. Fast, modern, and perfectly suited for streaming AI chunks via WebSockets.
*   **Local AI:** Ollama running the Qwen family. Hand-selected for having the best performance-to-size ratio on consumer hardware (Apple Metal GPU on macOS, CPU/CUDA on Linux).
*   **Audio AI:** Moonshine Voice (STT) and Kokoro (TTS) running natively via PyTorch. Avoids heavy C++ compilation steps while maintaining real-time streaming latency.
*   **Data Storage:** SQLite (structured data) and ChromaDB (vector embeddings). No background database daemons required.

All inference runs locally via Ollama with hardware-appropriate acceleration (Metal on macOS, CUDA on Linux with NVIDIA GPU, CPU otherwise). See [Model Selection](./model-selection.md) for detailed model justification.
