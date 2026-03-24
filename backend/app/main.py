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
    app.mount("/_next", StaticFiles(directory=os.path.join(frontend_dist, "_next")), name="next_assets")
    
    @app.middleware("http")
    async def fallback_to_index(request, call_next):
        response = await call_next(request)
        if response.status_code == 404 and not request.url.path.startswith("/api"):
            path = request.url.path.strip("/")
            
            if not path:
                path = "index.html"
            elif not path.endswith(".html"):
                if os.path.exists(os.path.join(frontend_dist, f"{path}.html")):
                    path = f"{path}.html"
                elif not os.path.exists(os.path.join(frontend_dist, path)):
                    path = "index.html"
            
            filepath = os.path.join(frontend_dist, path)
            if os.path.exists(filepath):
                return FileResponse(filepath)
        return response
else:
    logger.warning("Frontend static build not found. Only API is active.")
