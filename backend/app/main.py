"""
TinkerPilot FastAPI application.
Main entry point for the backend server.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_config, ensure_directories
from app.db.sqlite import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic."""
    logger.info("Starting TinkerPilot backend...")
    ensure_directories()
    init_db()

    # Pre-warm the daily digest in the background so the UI loads instantly
    import threading
    from app.api.digest import prewarm_digest
    threading.Thread(target=prewarm_digest, daemon=True).start()

    config = get_config()
    logger.info(f"Server config: host={config.host}, port={config.port}")
    logger.info(f"LLM model: {config.llm.model_name} (via Ollama)")
    logger.info(f"Embedding model: {config.embedding.model_name} (via Ollama)")
    yield
    logger.info("Shutting down TinkerPilot backend.")


app = FastAPI(
    title="TinkerPilot",
    description="Local AI assistant for developers",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS for frontend at localhost:3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check
@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "tinkerpilot"}


# Import and register routers
from app.api.chat import router as chat_router
from app.api.documents import router as documents_router
from app.api.meetings import router as meetings_router
from app.api.tasks import router as tasks_router
from app.api.digest import router as digest_router
from app.api.search import router as search_router
from app.api.utils import router as utils_router

app.include_router(chat_router, prefix="/api")
app.include_router(documents_router, prefix="/api")
app.include_router(meetings_router, prefix="/api")
app.include_router(tasks_router, prefix="/api")
app.include_router(digest_router, prefix="/api")
app.include_router(search_router, prefix="/api")
app.include_router(utils_router, prefix="/api")

# --- Serve Frontend Static Files ---
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.config import PROJECT_ROOT

frontend_dist = os.path.join(PROJECT_ROOT, "frontend", "out")
if os.path.exists(frontend_dist):
    next_assets_dir = os.path.join(frontend_dist, "_next")
    if os.path.exists(next_assets_dir):
        # Serve the extremely heavy _next JS chunks via high-speed native StaticFiles router
        app.mount("/_next", StaticFiles(directory=next_assets_dir), name="next_assets")

    # Native catch-all route for SPA navigation (replaces slow middleware)
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        if full_path.startswith("api/"):
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="API route not found")
            
        if not full_path:
            full_path = "index.html"
            
        # Try direct file (e.g., favicon.ico)
        filepath = os.path.join(frontend_dist, full_path)
        if os.path.exists(filepath) and os.path.isfile(filepath):
            return FileResponse(filepath)
            
        # Try Next.js static exported HTML file (e.g. /chat -> chat.html)
        html_filepath = os.path.join(frontend_dist, f"{full_path}.html")
        if os.path.exists(html_filepath) and os.path.isfile(html_filepath):
            return FileResponse(html_filepath)
            
        # Final fallback to root index.html
        index_filepath = os.path.join(frontend_dist, "index.html")
        if os.path.exists(index_filepath) and os.path.isfile(index_filepath):
            return FileResponse(index_filepath)
            
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="File not found")
else:
    logger.warning("Frontend static build not found. Only API is active.")
