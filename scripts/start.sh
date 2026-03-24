#!/bin/bash
# TinkerPilot - Start everything with one command
# Launches Ollama (if needed), backend, and frontend

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

info() { echo -e "${GREEN}[OK]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

cleanup() {
    echo ""
    echo "Shutting down servers..."
    if [ ! -z "$BACKEND_PID" ]; then kill -TERM $BACKEND_PID 2>/dev/null || true; fi
    
    # npm spawns child processes, we need to kill the process group or use pkill
    if [ ! -z "$FRONTEND_PID" ]; then 
        pkill -P $FRONTEND_PID 2>/dev/null || true
        kill -TERM $FRONTEND_PID 2>/dev/null || true
    fi
    echo "Done."
    exit 0
}
trap cleanup SIGINT SIGTERM

# ─── Check setup was run ─────────────────────────────────────

if [ ! -d "$BACKEND_DIR/.venv" ]; then
    error "Backend not set up. Run ./scripts/setup.sh first."
    exit 1
fi

if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    error "Frontend not set up. Run ./scripts/setup.sh first."
    exit 1
fi

# ─── Ensure Ollama is running ─────────────────────────────────

if ! command -v ollama &> /dev/null; then
    error "Ollama not installed. Run ./scripts/setup.sh first."
    exit 1
fi

if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
    info "Starting Ollama..."
    ollama serve &> /dev/null &
    for i in $(seq 1 15); do
        if curl -s http://localhost:11434/api/tags &> /dev/null; then break; fi
        sleep 1
    done
    if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
        error "Ollama failed to start."
        exit 1
    fi
fi
info "Ollama running"

# ─── Start backend ────────────────────────────────────────────

info "Starting backend on http://localhost:8000..."
cd "$BACKEND_DIR"
source .venv/bin/activate
python -m cli.main serve &
BACKEND_PID=$!

# Wait for backend to be ready
for i in $(seq 1 30); do
    if curl -s http://localhost:8000/api/health &> /dev/null; then break; fi
    sleep 1
done

if curl -s http://localhost:8000/api/health &> /dev/null; then
    info "Backend ready"
else
    error "Backend failed to start. Check logs above."
    exit 1
fi

# ─── Start frontend ──────────────────────────────────────────

info "Starting frontend on http://localhost:3000..."
cd "$FRONTEND_DIR"
npm run dev &
FRONTEND_PID=$!

sleep 3

echo ""
echo "============================================"
echo -e "  ${GREEN}TinkerPilot is running!${NC}"
echo ""
echo "    Web UI:  http://localhost:3000"
echo "    API:     http://localhost:8000/api/health"
echo ""
echo "  Press Ctrl+C to stop."
echo "============================================"

# Wait for any child to exit
wait
