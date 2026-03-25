---
sidebar_position: 5
title: Implementation
---
TinkerPilot is built with a modular architecture that allows for easy feature addition and maintenance. Project structure disaggrate core components into separate modules, core AI logic and execution is handled by `core` module, and cli is handled by `cli` module.

Below is the complete project structure outlining the core components and their responsibilities:

```
TinkerPilot
├── backend/            # Python FastAPI backend
│   ├── app/            # Core application logic
│   │   ├── api/        # API endpoint routers
│   │   ├── core/       # Core AI and business logic (RAG, STT, TTS)
│   │   ├── db/         # Database models and connections
│   │   ├── integrations/ # Integrations with other services (Obsidian, Apple Notes)
│   │   ├── main.py     # FastAPI application entry point
│   │   └── config.py   # Application configuration
│   ├── cli/            # CLI logic (Typer)
│   └── tests/          # Backend tests
├── frontend/           # Next.js frontend
│   ├── src/
│   │   ├── app/        # Next.js App Router pages
│   │   ├── components/ # Reusable React components
│   │   └── lib/        # API communication and utility functions
│   ├── public/         # Static assets
│   └── next.config.js  # Next.js configuration
├── scripts/            # Helper scripts for setup and execution
│   ├── setup.sh        # Development environment setup
│   └── start.sh        # Start script for development
└── docs-site/          # Docusaurus documentation 
```

## `backend/`

This directory contains all the Python code for the backend server.

-   **`app/`**: This is the main application directory.
    -   **`api/`**: Each file in this directory defines a set of related API endpoints using FastAPI's `APIRouter`.
    -   **`core/`**: This is where the core business logic of the application resides. This includes the RAG pipeline, speech-to-text, text-to-speech, and other AI-powered features.
    -   **`db/`**: This directory contains the database models (`models.py`), the SQLite connection logic (`sqlite.py`), and the ChromaDB vector database connection logic (`vector.py`).
    -   **`integrations/`**: This directory contains the code for integrating with external services like Obsidian and Apple Notes.
    -   **`main.py`**: The entry point for the FastAPI application.
    -   **`config.py`**: Defines the application's configuration.
-   **`cli/`**: This directory contains the code for the command-line interface, which is built with [Typer](https://typer.tiangolo.com/).
-   **`tests/`**: Contains the backend tests (currently empty).

For more details on backend and local AI implementation, see [Backend Implementation](./backend.md) and [Local AI](./local-ai.md).

## `frontend/`

This directory contains the Next.js frontend application.

-   **`src/app/`**: This directory uses the Next.js App Router to define the application's pages.
-   **`src/components/`**: This directory contains reusable React components.
-   **`src/lib/`**: This directory contains utility functions and the all-important `api.ts` file, which handles communication with the backend.
-   **`public/`**: Contains static assets like images and fonts.
-   **`next.config.js`**: The configuration file for the Next.js application.

For more details on frontend implementation, see [Frontend Implementation](./frontend.md)

## `scripts/`

This directory contains various helper scripts for setting up and running the application.

-   **`setup.sh`**: Sets up the local development environment.
-   **`start.sh`**: Starts all the necessary services for local development.

## `docs-site/`

Contains the Docusaurus documentation website that you are currently viewing.
