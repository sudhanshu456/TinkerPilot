#!/bin/bash
# TinkerPilot Interactive Uninstaller
# Usage: curl -fsSL https://raw.githubusercontent.com/username/tinkerpilot/main/uninstall.sh | bash

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "============================================"
echo "  TinkerPilot - Uninstaller"
echo "============================================"
echo ""

read -p "Are you sure you want to uninstall TinkerPilot? (y/N) " confirm < /dev/tty
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "Uninstallation cancelled."
    exit 0
fi

# 1. Remove the global 'tp' command
echo -e "\n${BLUE}[1/3] Removing global command...${NC}"
if [ -f "/usr/local/bin/tp" ]; then
    sudo rm -f "/usr/local/bin/tp" 2>/dev/null || rm -f "/usr/local/bin/tp"
    echo -e "${GREEN}Removed /usr/local/bin/tp${NC}"
elif [ -f "$HOME/.local/bin/tp" ]; then
    rm -f "$HOME/.local/bin/tp"
    echo -e "${GREEN}Removed $HOME/.local/bin/tp${NC}"
else
    echo "Global 'tp' command not found. Skipping."
fi

# 2. Remove application files and (optionally) data
echo -e "\n${BLUE}[2/3] Removing application files...${NC}"
echo "Your TinkerPilot application environment is stored in ~/.tinkerpilot/app"
echo "Your configuration and database (tasks, meetings, transcripts) are stored in ~/.tinkerpilot"
echo ""
read -p "Do you want to completely DELETE all your data and configuration? (y/N) " wipe_data < /dev/tty

# Track if we are wiping everything before we actually wipe it so we can read the ollama marker
WIPE_ALL=false
if [[ "$wipe_data" =~ ^[Yy]$ ]]; then
    WIPE_ALL=true
fi

# 3. Remove Ollama models/app
echo -e "\n${BLUE}[3/3] AI Engine & Models...${NC}"
if [ -f "$HOME/.tinkerpilot/.tp_installed_ollama" ]; then
    echo "TinkerPilot originally installed Ollama on your system to run AI models locally."
    read -p "Do you want to completely uninstall Ollama and remove all models? (y/N) " remove_ollama < /dev/tty
    if [[ "$remove_ollama" =~ ^[Yy]$ ]]; then
        echo "Uninstalling Ollama..."
        if [ "$(uname)" == "Darwin" ]; then
            brew uninstall ollama 2>/dev/null || true
        else
            # On Linux, Ollama installs via curl script to /usr/local/bin
            sudo rm -f /usr/local/bin/ollama 2>/dev/null || true
            sudo systemctl stop ollama 2>/dev/null || true
            sudo systemctl disable ollama 2>/dev/null || true
            sudo rm -f /etc/systemd/system/ollama.service 2>/dev/null || true
            rm -rf "$HOME/.ollama" 2>/dev/null || true
        fi
        rm -f "$HOME/.tinkerpilot/.tp_installed_ollama"
        echo -e "${GREEN}Ollama has been uninstalled.${NC}"
    else
        echo "Kept Ollama and its models."
    fi
else
    echo "Ollama was already installed on your system before TinkerPilot."
    echo "TinkerPilot downloaded Qwen2.5 (3B) and Qwen3-Embedding (0.6B) (~2.6GB total)."
    read -p "Do you want to delete ONLY these specific models to free up space? (y/N) " remove_models < /dev/tty
    
    if [[ "$remove_models" =~ ^[Yy]$ ]]; then
        if command -v ollama &> /dev/null; then
            if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
                ollama serve &> /dev/null &
                OLLAMA_PID=$!
                sleep 2
            fi
            
            echo "Removing TinkerPilot models..."
            ollama rm qwen2.5:3b 2>/dev/null || true
            ollama rm qwen3-embedding:0.6b 2>/dev/null || true
            echo -e "${GREEN}Removed Qwen models. Ollama remains installed.${NC}"
            
            if [ ! -z "$OLLAMA_PID" ]; then kill $OLLAMA_PID 2>/dev/null || true; fi
        else
            echo "Ollama not found. Skipping."
        fi
    else
        echo "Kept AI models."
    fi
fi

# Finally, execute the data wipe if requested
if [ "$WIPE_ALL" = true ]; then
    rm -rf "$HOME/.tinkerpilot"
    echo -e "\n${GREEN}Removed all TinkerPilot data and virtual environment ($HOME/.tinkerpilot).${NC}"
else
    rm -rf "$HOME/.tinkerpilot/app"
    echo -e "\n${GREEN}Removed application virtual environment ($HOME/.tinkerpilot/app).${NC}"
    echo -e "${YELLOW}Your personal data and configuration were safely kept in $HOME/.tinkerpilot${NC}"
fi

echo ""
echo "============================================"
echo -e "${GREEN}TinkerPilot has been successfully uninstalled!${NC}"
echo "============================================"
echo ""
