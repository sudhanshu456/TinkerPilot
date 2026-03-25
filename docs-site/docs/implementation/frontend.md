---
sidebar_position: 2
title: Frontend
---

# Frontend Implementation

The TinkerPilot frontend is a modern web application built with [Next.js](https://nextjs.org/) and [React](https://react.dev/). It is designed to be a simple, fast, and responsive user interface for interacting with the backend services.

## Tech Stack

-   **Framework:** [Next.js](https://nextjs.org/) (React)
-   **Language:** [TypeScript](https://www.typescriptlang.org/)
-   **Styling:** The project uses CSS variables for styling, defined in `src/app/globals.css`. There is no complex CSS-in-JS library or component library, keeping the frontend lightweight and easy to customize.

The frontend is configured for `output: export` in `next.config.js`, which means it is pre-built into a set of static HTML, CSS, and JavaScript files. This allows it to be served by any web server, and in TinkerPilot's case, it is served directly by the FastAPI backend in a production environment.

## Project Structure

The frontend code is located in the `frontend` directory. The most important files and directories are:

-   `frontend/src/app/`: This directory contains the main pages of the application. Next.js uses a file-based routing system, so each `page.tsx` file in this directory corresponds to a specific route.
    -   `layout.tsx`: The root layout for the application, which includes the `Sidebar` component.
    -   `page.tsx`: The main dashboard page.
    -   `chat/page.tsx`: The chat interface.
    -   `meetings/page.tsx`: The meetings page.
    -   And so on for `tasks`, `search`, and `settings`.
-   `frontend/src/components/`: This directory contains reusable React components, such as the `Sidebar.tsx`.
-   `frontend/src/lib/`: This directory contains library code, utility functions, and API communication logic.
    -   `api.ts`: This is a crucial file that contains all the functions for making API calls to the backend.

## API Communication

All communication with the backend is handled through the functions in `frontend/src/lib/api.ts`. This file provides a clean and typed interface for interacting with the FastAPI endpoints.

### Fetching Data

The `apiFetch` function is a generic wrapper around the `fetch` API that handles common tasks like setting headers and error handling. All other API functions use this wrapper to make requests to the backend.

### WebSocket Communication

For real-time communication in the chat interface, the frontend uses a WebSocket connection. The `createChatWebSocket` function in `api.ts` sets up the WebSocket and defines handlers for different message types (`token`, `sources`, `done`, `error`).

## Routing

The application uses the Next.js App Router. The routes are defined by the directory structure in `src/app`:

-   `/`: The dashboard page (`src/app/page.tsx`)
-   `/chat`: The chat page (`src/app/chat/page.tsx`)
-   `/meetings`: The meetings page (`src/app/meetings/page.tsx`)
-   `/tasks`: The tasks page (`src/app/tasks/page.tsx`)
-   `/search`: The search page (`src/app/search/page.tsx`)
-   `/settings`: The settings page (`src/app/settings/page.tsx`)

## State Management

The frontend uses React's built-in hooks, primarily `useState` and `useEffect`, for managing component-level state. There is no global state management library like Redux or Zustand, which keeps the state management simple and localized to the components that need it.
