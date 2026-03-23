#!/bin/bash
# TinkerPilot Setup Script
# Sets up the complete development environment on macOS

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

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

info() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ─── Check Prerequisites ─────────────────────────────────────

info "Checking prerequisites..."

# Python
if ! command -v python3 &> /dev/null; then
    error "Python 3 not found. Install it: brew install python@3.11"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
info "Python: $PYTHON_VERSION"

# Node.js
if ! command -v node &> /dev/null; then
    error "Node.js not found. Install it: brew install node"
    exit 1
fi

NODE_VERSION=$(node --version)
info "Node.js: $NODE_VERSION"

# Git
if ! command -v git &> /dev/null; then
    warn "Git not found. Some features (git-digest) won't work."
fi

# Check macOS for Metal support
if [[ "$(uname)" == "Darwin" ]]; then
    ARCH=$(uname -m)
    if [[ "$ARCH" == "arm64" ]]; then
        info "Platform: macOS Apple Silicon (Metal GPU acceleration available)"
        CMAKE_METAL_FLAG="-DGGML_METAL=on"
    else
        info "Platform: macOS Intel"
        CMAKE_METAL_FLAG=""
    fi
else
    info "Platform: $(uname -s)"
    CMAKE_METAL_FLAG=""
fi

echo ""

# ─── Create User Data Directory ──────────────────────────────

info "Creating data directories..."
mkdir -p ~/.tinkerpilot/data/{chroma,audio,uploads}
info "Data directory: ~/.tinkerpilot/"

# ─── Backend Setup ────────────────────────────────────────────

echo ""
info "Setting up Python backend..."

cd "$BACKEND_DIR"

# Create virtual environment
if [ ! -d ".venv" ]; then
    info "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate
source .venv/bin/activate
info "Virtual environment activated."

# Install llama-cpp-python with Metal support
info "Installing llama-cpp-python with Metal GPU acceleration..."
info "This may take a few minutes (compiling from source)..."

if [[ -n "$CMAKE_METAL_FLAG" ]]; then
    CMAKE_ARGS="$CMAKE_METAL_FLAG" pip install llama-cpp-python --no-cache-dir 2>&1 | tail -5
else
    pip install llama-cpp-python --no-cache-dir 2>&1 | tail -5
fi

# Install remaining dependencies
info "Installing Python dependencies..."
pip install -e ".[dev]" 2>&1 | tail -5

info "Backend dependencies installed."

# ─── Download Models ──────────────────────────────────────────

echo ""
info "Downloading AI models..."
info "This will download ~2.1 GB of model files."
echo ""

python3 "$SCRIPT_DIR/download_models.py"

# ─── Frontend Setup ───────────────────────────────────────────

echo ""
info "Setting up Next.js frontend..."

cd "$FRONTEND_DIR"

if command -v npm &> /dev/null; then
    npm install 2>&1 | tail -5
    info "Frontend dependencies installed."
else
    warn "npm not found. Frontend setup skipped."
    warn "Install Node.js and run: cd frontend && npm install"
fi

# ─── Initialize Database ─────────────────────────────────────

echo ""
info "Initializing database..."

cd "$BACKEND_DIR"
source .venv/bin/activate

python3 -c "
import sys
sys.path.insert(0, '.')
from app.config import ensure_directories
from app.db.sqlite import init_db
ensure_directories()
init_db()
print('Database initialized.')
"

# ─── Done ─────────────────────────────────────────────────────

echo ""
echo "============================================"
echo -e "  ${GREEN}Setup Complete!${NC}"
echo "============================================"
echo ""
echo "  To start TinkerPilot:"
echo ""
echo "  1. Start the backend:"
echo "     cd backend"
echo "     source .venv/bin/activate"
echo "     python -m cli.main serve"
echo ""
echo "  2. Start the frontend (in another terminal):"
echo "     cd frontend"
echo "     npm run dev"
echo ""
echo "  3. Open http://localhost:3000"
echo ""
echo "  CLI usage (with venv activated):"
echo "     python -m cli.main ask 'how does auth work?'"
echo "     python -m cli.main ingest ~/my-project"
echo "     python -m cli.main tasks"
echo "     python -m cli.main --help"
echo ""
echo "============================================"
