#!/bin/bash
# TinkerPilot Interactive Installer
# Usage: curl -fsSL https://raw.githubusercontent.com/username/tinkerpilot/main/install.sh | bash

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info() { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }
step() { echo -e "\n${BLUE}[STEP]${NC} $1"; }

echo "============================================"
echo "  TinkerPilot - Installer"
echo "  Local AI Assistant for Developers"
echo "============================================"
echo ""

if [ "$(uname)" != "Darwin" ] && [ "$(uname)" != "Linux" ]; then
    error "TinkerPilot currently supports macOS and Linux."
fi

# Detect package manager
PKG_MGR=""
if [ "$(uname)" == "Darwin" ]; then
    PKG_MGR="brew"
elif command -v apt-get &> /dev/null; then
    PKG_MGR="apt"
elif command -v yum &> /dev/null; then
    PKG_MGR="yum"
else
    warn "Unsupported Linux distribution. You may need to manually install system dependencies."
fi

INSTALL_DIR="${HOME}/.tinkerpilot/app"
CONFIG_DIR="${HOME}/.tinkerpilot"
mkdir -p "$CONFIG_DIR"

step "Checking system dependencies..."

# Python
PYTHON_CMD=""
check_python_version() {
    local cmd="$1"
    if command -v "$cmd" &> /dev/null; then
        local version=$("$cmd" -c 'import sys; print(".".join(map(str, sys.version_info[:2])))' 2>/dev/null || true)
        if [[ "$version" == "3.10" || "$version" == "3.11" || "$version" == "3.12" ]]; then
            echo "$cmd"
            return 0
        fi
    fi
    return 0
}

for cmd in python3.12 python3.11 python3.10 python3 python; do
    VALID_PY=$(check_python_version "$cmd" || true)
    if [ -n "$VALID_PY" ]; then
        PYTHON_CMD="$VALID_PY"
        break
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    warn "A compatible Python version (3.10 - 3.12) was not found."
    if [ "$PKG_MGR" == "brew" ]; then
        info "Installing Python 3.12 via Homebrew..."
        brew install python@3.12
        PYTHON_CMD="$(brew --prefix python@3.12)/bin/python3.12"
    elif [ "$PKG_MGR" == "apt" ]; then
        info "Installing Python 3 and venv via APT..."
        sudo apt-get update && sudo apt-get install -y python3 python3-venv python3-pip
        PYTHON_CMD="python3"
    elif [ "$PKG_MGR" == "yum" ]; then
        info "Installing Python 3 via YUM..."
        sudo yum install -y python3
        PYTHON_CMD="python3"
    else
        error "Please manually install Python 3.10, 3.11, or 3.12 before continuing."
    fi
else
    info "Found compatible Python: $PYTHON_CMD"
fi

# espeak-ng (TTS)
if ! command -v espeak-ng &> /dev/null; then
    warn "espeak-ng (required for TTS) is missing."
    if [ "$PKG_MGR" == "brew" ]; then
        info "Installing espeak-ng..."
        brew install espeak-ng
    elif [ "$PKG_MGR" == "apt" ]; then
        info "Installing espeak-ng via APT..."
        sudo apt-get install -y espeak-ng
    elif [ "$PKG_MGR" == "yum" ]; then
        info "Installing espeak-ng via YUM..."
        sudo yum install -y espeak-ng
    fi
fi

# ffmpeg (Audio Processing)
if ! command -v ffmpeg &> /dev/null; then
    warn "ffmpeg (required for Audio processing) is missing."
    if [ "$PKG_MGR" == "brew" ]; then
        info "Installing ffmpeg..."
        brew install ffmpeg
    elif [ "$PKG_MGR" == "apt" ]; then
        info "Installing ffmpeg via APT..."
        sudo apt-get install -y ffmpeg
    elif [ "$PKG_MGR" == "yum" ]; then
        info "Installing ffmpeg via YUM..."
        sudo yum install -y ffmpeg
    fi
fi

# Smarter Ollama Installation
if ! command -v ollama &> /dev/null; then
    info "Installing Ollama (local AI engine)..."
    if [ "$PKG_MGR" == "brew" ]; then
        brew install ollama
    else
        curl -fsSL https://ollama.com/install.sh | sh
    fi
    # Mark that TinkerPilot is the one that installed Ollama
    touch "$CONFIG_DIR/.tp_installed_ollama"
else
    info "Ollama is already installed."
    # Ensure the marker doesn't exist if they already had it
    rm -f "$CONFIG_DIR/.tp_installed_ollama"
fi

if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
    info "Starting Ollama server in background..."
    ollama serve &> /dev/null &
    sleep 3
fi

step "Downloading TinkerPilot..."
if [ -d "$INSTALL_DIR" ]; then
    info "Updating existing installation at $INSTALL_DIR..."
    cd "$INSTALL_DIR"
    git pull origin main --quiet || true
else
    info "Cloning to $INSTALL_DIR..."
    git clone https://github.com/sudhanshu456/tinkerpilot.git "$INSTALL_DIR" --quiet
    cd "$INSTALL_DIR"
fi

step "Configuring TinkerPilot..."
CONFIG_FILE="$CONFIG_DIR/config.yaml"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Let's set up your preferences!"
    echo ""

    # Read from /dev/tty so prompts work when script is piped via curl | bash
    read -p "1. Enter your Hugging Face Token (or press Enter to skip): " HF_TOKEN < /dev/tty

    echo "2. Where do you keep your local Markdown notes? (e.g., Obsidian/Logseq vault)"
    read -p "   Enter full path (or press Enter to skip): " OBSIDIAN_PATH < /dev/tty

    if [ "$(uname)" == "Darwin" ]; then
        echo -n "3. Do you want to enable Apple Notes indexing? (y/N): "
        read ENABLE_NOTES < /dev/tty
        if [[ "$ENABLE_NOTES" =~ ^[Yy]$ ]]; then
            NOTES_BOOL="true"
        else
            NOTES_BOOL="false"
        fi
    else
        NOTES_BOOL="false" # Disable Apple Notes inherently on Linux
    fi

    # Expand tilde in path if provided
    OBSIDIAN_PATH="${OBSIDIAN_PATH/#\~/$HOME}"

    echo "Generating config file at $CONFIG_FILE..."
    cat > "$CONFIG_FILE" << EOF
hf_token: "${HF_TOKEN}"

llm:
  model_name: "qwen2.5:3b"
  temperature: 0.7

embedding:
  model_name: "qwen3-embedding:0.6b"

whisper:
  model_size: small
  language: en

rag:
  chunk_size: 512
  top_k: 5

integrations:
  enable_apple_notes: ${NOTES_BOOL}
EOF

    # Append obsidian path as a separate step to avoid YAML indentation issues
    if [ -n "$OBSIDIAN_PATH" ]; then
        # Insert obsidian_vault_path before enable_apple_notes
        if [ "$(uname)" == "Darwin" ]; then
            sed -i '' "/enable_apple_notes/i\\
  obsidian_vault_path: \\"${OBSIDIAN_PATH}\\"" "$CONFIG_FILE"
        else
            sed -i "/enable_apple_notes/i\\  obsidian_vault_path: \"${OBSIDIAN_PATH}\"" "$CONFIG_FILE"
        fi
    fi
else
    info "Config file already exists at $CONFIG_FILE. Skipping setup."
fi

step "Setting up backend..."
cd "$INSTALL_DIR/backend" || error "Backend directory not found at $INSTALL_DIR/backend"

if [ -d ".venv" ]; then
    echo "An existing backend virtual environment was found."
    echo "A clean install prevents Python version conflicts, but takes longer."
    read -p "  Perform clean install of backend dependencies? (Y/n): " CLEAN_VENV < /dev/tty
    if [[ ! "$CLEAN_VENV" =~ ^[Nn]$ ]]; then
        info "Wiping old virtual environment..."
        rm -rf .venv
    else
        info "Keeping existing virtual environment (Not recommended if Python version changed)."
    fi
fi

$PYTHON_CMD -m venv .venv
source .venv/bin/activate
pip install --default-timeout=100 --upgrade pip
pip install --default-timeout=100 -e .
info "Python environment ready."

step "Setting up frontend UI..."
if ! command -v node &> /dev/null; then
    warn "Node.js is missing (required to build UI)."
    if [ "$PKG_MGR" == "brew" ]; then
        info "Installing Node.js via Homebrew..."
        brew install node
    elif [ "$PKG_MGR" == "apt" ]; then
        info "Installing Node.js via APT..."
        curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
        sudo apt-get install -y nodejs
    elif [ "$PKG_MGR" == "yum" ]; then
        info "Installing Node.js via YUM..."
        curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash -
        sudo yum install -y nodejs
    else
        error "Please manually install Node.js 18+ before continuing."
    fi
fi
cd "$INSTALL_DIR/frontend"
npm install --silent
npm run build --silent
info "Frontend built as static app."

cd "$INSTALL_DIR/backend"
./.venv/bin/python -c "
import sys; sys.path.insert(0, '.')
from app.config import ensure_directories
from app.db.sqlite import init_db
ensure_directories()
init_db()
"

step "Creating 'tp' global command..."
BIN_DIR="/usr/local/bin"
if [ ! -w "$BIN_DIR" ]; then
    BIN_DIR="$HOME/.local/bin"
    mkdir -p "$BIN_DIR"
    if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
        warn "Please add $BIN_DIR to your PATH"
    fi
fi

cat > "$BIN_DIR/tp" << EOL
#!/bin/bash
cd "$INSTALL_DIR/backend"
source .venv/bin/activate
exec python -m cli.main "\$@"
EOL
chmod +x "$BIN_DIR/tp"
info "Created global command: ${BIN_DIR}/tp"

step "Downloading AI Models (this will take a few minutes)..."
ollama pull qwen2.5:3b
ollama pull qwen3-embedding:0.6b

echo ""
echo "============================================"
echo -e "${GREEN}TinkerPilot Installed Successfully!${NC}"
echo "============================================"
echo ""
echo "To start the web interface, run:"
echo -e "  ${BLUE}tp serve${NC}"
echo ""
echo "To chat from the terminal, run:"
echo -e "  ${BLUE}tp ask \"How do I write a bash script?\"${NC}"
echo ""
