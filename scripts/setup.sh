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

# Python — need 3.10-3.13 (3.14+ is too new for llama-cpp-python / ML packages)
PYTHON_CMD=""
for candidate in python3.12 python3.13 python3.11 python3.10 python3; do
    if command -v "$candidate" &> /dev/null; then
        PY_VER=$("$candidate" --version 2>&1 | awk '{print $2}')
        PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)
        if [[ "$PY_MINOR" -ge 10 && "$PY_MINOR" -le 13 ]]; then
            PYTHON_CMD="$candidate"
            break
        fi
    fi
done

if [[ -z "$PYTHON_CMD" ]]; then
    error "No compatible Python found (need 3.10-3.13)."
    error "Python 3.14+ is too new — ML packages don't support it yet."
    error "Install a compatible version: brew install python@3.12"
    exit 1
fi

PYTHON_VERSION=$("$PYTHON_CMD" --version 2>&1 | awk '{print $2}')
info "Python: $PYTHON_VERSION ($PYTHON_CMD)"

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

# CMake (required for compiling llama-cpp-python)
if ! command -v cmake &> /dev/null; then
    error "CMake not found. Install it: brew install cmake"
    exit 1
fi
info "CMake: $(cmake --version | head -1 | awk '{print $3}')"

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

# Validate ccache if present (broken ccache is a common build-killer)
if command -v ccache &> /dev/null; then
    if ! ccache --version &> /dev/null; then
        warn "ccache is installed but broken (likely a stale dylib)."
        warn "Attempting to fix: brew reinstall ccache"
        brew reinstall ccache 2>&1 | tail -3
        if ! ccache --version &> /dev/null; then
            warn "ccache still broken. Disabling it for compilation."
            export GGML_CCACHE=OFF
        else
            info "ccache fixed."
        fi
    fi
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

# Remove old venv if created with wrong Python version
if [ -d ".venv" ]; then
    VENV_PY_VER=$(.venv/bin/python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
    WANT_PY_VER=$("$PYTHON_CMD" --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
    if [[ "$VENV_PY_VER" != "$WANT_PY_VER" ]]; then
        warn "Existing venv uses Python $VENV_PY_VER, need $WANT_PY_VER. Recreating..."
        rm -rf .venv
    fi
fi

# Create virtual environment
if [ ! -d ".venv" ]; then
    info "Creating virtual environment with $PYTHON_CMD..."
    "$PYTHON_CMD" -m venv .venv
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

python "$SCRIPT_DIR/download_models.py"

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

python -c "
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
