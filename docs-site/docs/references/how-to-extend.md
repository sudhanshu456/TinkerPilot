---
sidebar_position: 7
title: How to extend TinkerPilot
---
TinkerPilot's architecture is built to be easily extensible. Because it uses FastAPI for the backend and a Typer CLI, adding new tools involves creating core logic, exposing it via an API endpoint, and optionally binding it to a CLI command or a frontend.

This guide provides instructions and examples for developers who want to extend TinkerPilot with new features.

To setup the local development environment, follow the below steps:

## Local Setup

If you want to edit the code or run TinkerPilot in development mode (with hot-reloading Next.js):

```bash
git clone <repo-url> TinkerPilot
cd TinkerPilot
./scripts/setup.sh      # macOS (uses Homebrew)
```

### Running in Development Mode

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

In local development to run `tp` commands, you need to activate the virtual environment first: `cd backend && source .venv/bin/activate && tp <cmd>`.

## Example 1: Extending the Backend & CLI (`git-digest`)

Let's walk through how a real feature `tp git-digest` was added to TinkerPilot. The goal of this feature is to read the git log of a directory, pass it to the local LLM, and return a summarized digest.

### 1. Add Core Logic (`backend/app/core/`)

First, we need the actual business logic that fetches git logs and calls the LLM. You would typically create a new file or add to an existing core utility file.

```python
# backend/app/core/git_utils.py
import subprocess
from app.core.llm import generate

def get_git_digest(repo_path: str, num_commits: int = 20) -> str:
    # 1. Fetch the git log using a shell command
    cmd = ["git", "-C", repo_path, "log", f"-n {num_commits}", "--oneline"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise ValueError("Not a valid git repository or git failed.")
        
    git_log = result.stdout
    
    # 2. Ask the LLM to summarize it
    prompt = f"Summarize the following recent git commits into a readable digest:\n\n{git_log}"
    system_prompt = "You are an expert developer. Summarize git logs clearly."
    
    digest = generate(prompt, system_prompt=system_prompt)
    return digest
```

### 2. Expose an API Endpoint (`backend/app/api/`)

Next, we expose this function via a FastAPI endpoint so both the Web UI and the CLI can call it over HTTP. This goes into a router, for instance `backend/app/api/utils.py`.

```python
# backend/app/api/utils.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.git_utils import get_git_digest

router = APIRouter()

class GitDigestRequest(BaseModel):
    repo_path: str
    num_commits: int = 20

@router.post("/utils/git-digest")
async def api_git_digest(request: GitDigestRequest):
    try:
        digest = get_git_digest(request.repo_path, request.num_commits)
        return {"digest": digest}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

Ensure your router is included in `backend/app/main.py`:
```python
from app.api.utils import router as utils_router
app.include_router(utils_router, prefix="/api")
```

### 3. Add a CLI Command (`backend/cli/main.py`)

Finally, we bind this endpoint to a new CLI command using Typer. The CLI makes an HTTP request to the local FastAPI server.

```python
# backend/cli/main.py
import typer
import httpx
from rich import print

app = typer.Typer()

@app.command(name="git-digest")
def git_digest(
    repo_path: str = typer.Argument(..., help="Path to the git repository"),
    num_commits: int = typer.Option(20, help="Number of commits to analyze")
):
    """Generate a summary of recent git commit activity."""
    # Communicate with the running local API
    response = httpx.post(
        "http://localhost:8000/api/utils/git-digest",
        json={"repo_path": repo_path, "num_commits": num_commits},
        timeout=60.0
    )
    
    if response.status_code == 200:
        print(f"\n[bold green]Git Digest for {repo_path}[/bold green]")
        print(response.json()["digest"])
    else:
        print(f"[red]Error:[/red] {response.json().get('detail', 'Unknown error')}")
```

Now, users can type `tp git-digest /path/to/repo` in their terminal, and the command will flow through the CLI -> API -> Core Logic -> LLM.

---

## Example 2: Adding a Frontend Feature (Calendar Integration)

Suppose you want to add a completely new feature: a **Calendar Dashboard** that displays your daily schedule and allows you to chat with the AI about your upcoming meetings.

Here is the step-by-step process of how you would extend TinkerPilot to support this:

### 1. Backend Data & API
First, you'd create the backend integration to fetch calendar events (e.g., parsing local `.ics` files or connecting to macOS EventKit).
*   **Core:** Create `backend/app/integrations/calendar.py` to fetch today's events.
*   **API:** Create `backend/app/api/calendar.py` with an endpoint `@router.get("/calendar/today")`.

### 2. Update Frontend API Client (`frontend/src/lib/api.ts`)
Add a new function to your frontend API client to fetch the calendar data.

```typescript
// frontend/src/lib/api.ts
export const getTodayEvents = () =>
  apiFetch<{ events: any[] }>('/calendar/today');
```

### 3. Create a New Next.js Page (`frontend/src/app/`)
Create a new directory and page component for the calendar view: `frontend/src/app/calendar/page.tsx`.

```tsx
// frontend/src/app/calendar/page.tsx
'use client';

import { useEffect, useState } from 'react';
import { getTodayEvents } from '@/lib/api';

export default function CalendarPage() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getTodayEvents()
      .then((data) => setEvents(data.events))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p>Loading calendar...</p>;

  return (
    <div>
      <h1>Today's Calendar</h1>
      <div className="event-list">
        {events.map((event, idx) => (
          <div key={idx} className="event-card">
            <h3>{event.title}</h3>
            <p>{event.time}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
```

### 4. Add the Page to the Sidebar
To make your new page accessible, open `frontend/src/components/Sidebar.tsx` and add a new navigation link to `/calendar`.

```tsx
// frontend/src/components/Sidebar.tsx
import Link from 'next/link';

// ... inside your sidebar component
<Link href="/calendar" className="nav-item">
  📅 Calendar
</Link>
```

### 5. Update Documentation
Finally, don't forget to update the Docusaurus documentation! 

---

By following this pattern: **Core Logic -> API Endpoint -> Interface (CLI or UI)**, you can build any capabilities you want into TinkerPilot while maintaining its clean, decoupled architecture.
