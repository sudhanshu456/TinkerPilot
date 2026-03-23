#!/bin/bash
# TinkerPilot Setup Script
# One-command setup for macOS. Installs everything needed.

set -e

echo "============================================"
echo "  TinkerPilot - Setup"
echo "  Local AI Assistant for Developers"
echo "============================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info() { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }
step() { echo -e "\n${GREEN}[STEP]${NC} $1"; }

# ─── 1. Check Prerequisites ─────────────────────────────────

step "Checking prerequisites..."

# Homebrew
if ! command -v brew &> /dev/null; then
    error "Homebrew not found. Install it first:"
    echo '  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
    exit 1
fi
info "Homebrew found"

# Python (any 3.10+ works — no C++ compilation needed)
PYTHON_CMD=""
for candidate in python3.12 python3.13 python3.11 python3.10 python3; do
    if command -v "$candidate" &> /dev/null; then
        PY_MINOR=$("$candidate" --version 2>&1 | awk '{print $2}' | cut -d. -f2)
        if [[ "$PY_MINOR" -ge 10 ]]; then
            PYTHON_CMD="$candidate"
            break
        fi
    fi
done

if [[ -z "$PYTHON_CMD" ]]; then
    error "Python 3.10+ not found. Install: brew install python@3.12"
    exit 1
fi
info "Python: $("$PYTHON_CMD" --version 2>&1 | awk '{print $2}') ($PYTHON_CMD)"

# Node.js
if ! command -v node &> /dev/null; then
    error "Node.js not found. Install: brew install node"
    exit 1
fi
info "Node.js: $(node --version)"

# ─── 2. Install Ollama ──────────────────────────────────────

step "Setting up Ollama (local AI inference)..."

if ! command -v ollama &> /dev/null; then
    info "Installing Ollama..."
    brew install ollama
else
    info "Ollama already installed: $(ollama --version 2>&1 | head -1)"
fi

# Start Ollama if not running
if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
    info "Starting Ollama server..."
    ollama serve &> /dev/null &
    OLLAMA_PID=$!
    for i in $(seq 1 30); do
        if curl -s http://localhost:11434/api/tags &> /dev/null; then
            break
        fi
        sleep 1
    done
    if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
        error "Ollama failed to start. Try running 'ollama serve' manually."
        exit 1
    fi
    info "Ollama server started"
else
    info "Ollama server already running"
fi

# ─── 3. Pull Models ─────────────────────────────────────────

step "Pulling AI models (this downloads ~2GB on first run)..."

# LLM
if ollama list 2>/dev/null | grep -q "qwen2.5:3b"; then
    info "LLM model already downloaded: qwen2.5:3b"
else
    info "Downloading LLM: qwen2.5:3b (~2GB)..."
    ollama pull qwen2.5:3b
    info "LLM model ready"
fi

# Embeddings
if ollama list 2>/dev/null | grep -q "nomic-embed-text"; then
    info "Embedding model already downloaded: nomic-embed-text"
else
    info "Downloading embedding model: nomic-embed-text (~274MB)..."
    ollama pull nomic-embed-text
    info "Embedding model ready"
fi

# ─── 4. Python Backend ──────────────────────────────────────

step "Setting up Python backend..."

cd "$BACKEND_DIR"

# Recreate venv if Python version changed
if [ -d ".venv" ]; then
    VENV_PY=$(.venv/bin/python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
    WANT_PY=$("$PYTHON_CMD" --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
    if [[ "$VENV_PY" != "$WANT_PY" ]]; then
        warn "Recreating venv (was Python $VENV_PY, need $WANT_PY)..."
        rm -rf .venv
    fi
fi

if [ ! -d ".venv" ]; then
    info "Creating virtual environment..."
    "$PYTHON_CMD" -m venv .venv
fi

source .venv/bin/activate

info "Installing Python dependencies..."
pip install --upgrade pip -q
pip install -e . 2>&1 | tail -3
info "Python dependencies installed"

# ─── 5. Frontend ─────────────────────────────────────────────

step "Setting up Next.js frontend..."

cd "$FRONTEND_DIR"
npm install --silent 2>&1 | tail -3
info "Frontend dependencies installed"

# ─── 6. Initialize Database ─────────────────────────────────

step "Initializing database..."

cd "$BACKEND_DIR"
source .venv/bin/activate

python -c "
import sys; sys.path.insert(0, '.')
from app.config import ensure_directories
from app.db.sqlite import init_db
ensure_directories()
init_db()
print('Database initialized.')
"
info "Database ready"

# ─── Done ─────────────────────────────────────────────────────

echo ""
echo "============================================"
echo -e "  ${GREEN}Setup Complete!${NC}"
echo "============================================"
echo ""
echo "  To start TinkerPilot (one command):"
echo ""
echo "    ./scripts/start.sh"
echo ""
echo "  Or start manually:"
echo ""
echo "    # Terminal 1: backend"
echo "    cd backend && source .venv/bin/activate"
echo "    python -m cli.main serve"
echo ""
echo "    # Terminal 2: frontend"
echo "    cd frontend && npm run dev"
echo ""
echo "    # Open http://localhost:3000"
echo ""
echo "============================================"
