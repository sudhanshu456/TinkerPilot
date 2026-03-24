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

read -p "Are you sure you want to uninstall TinkerPilot? (y/N) " confirm
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
echo "Your TinkerPilot application is stored in ~/.tinkerpilot/app"
echo "Your configuration and database (tasks, meetings, transcripts) are stored in ~/.tinkerpilot"
echo ""
read -p "Do you want to completely DELETE all your data and configuration? (y/N) " wipe_data

if [[ "$wipe_data" =~ ^[Yy]$ ]]; then
    rm -rf "$HOME/.tinkerpilot"
    echo -e "${GREEN}Removed all TinkerPilot data and code ($HOME/.tinkerpilot).${NC}"
else
    rm -rf "$HOME/.tinkerpilot/app"
    echo -e "${GREEN}Removed application code ($HOME/.tinkerpilot/app).${NC}"
    echo -e "${YELLOW}Your personal data and configuration were safely kept in $HOME/.tinkerpilot${NC}"
fi

# 3. Remove Ollama models (Optional)
echo -e "\n${BLUE}[3/3] AI Models...${NC}"
echo "TinkerPilot downloaded Qwen2.5 (3B) and Qwen3-Embedding (0.6B) via Ollama (~2.6GB total)."
echo "Other applications on your Mac might be using Ollama."
echo ""
echo "What would you like to do with Ollama?"
echo "  1) Keep Ollama and all models (Default)"
echo "  2) Delete ONLY the models TinkerPilot downloaded (Qwen2.5, Qwen3-Embedding)"
echo "  3) Completely uninstall Ollama from my Mac"
read -p "Select an option (1-3): " ollama_choice

if [[ "$ollama_choice" == "2" ]]; then
    if command -v ollama &> /dev/null; then
        echo "Removing TinkerPilot models..."
        # Start ollama temporarily if it's not running
        if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
            ollama serve &> /dev/null &
            OLLAMA_PID=$!
            sleep 2
        fi
        
        ollama rm qwen2.5:3b 2>/dev/null || true
        ollama rm qwen3-embedding:0.6b 2>/dev/null || true
        echo -e "${GREEN}Removed Qwen models. Ollama remains installed.${NC}"
        
        if [ ! -z "$OLLAMA_PID" ]; then
            kill $OLLAMA_PID 2>/dev/null || true
        fi
    else
        echo "Ollama not found. Skipping."
    fi
elif [[ "$ollama_choice" == "3" ]]; then
    if command -v brew &> /dev/null; then
        echo "Uninstalling Ollama via Homebrew..."
        brew uninstall ollama || true
        echo -e "${GREEN}Completely uninstalled Ollama.${NC}"
    else
        echo "Homebrew not found. Could not automatically uninstall Ollama."
    fi
else
    echo -e "${GREEN}Kept Ollama and all AI models.${NC}"
fi

echo ""
echo "============================================"
echo -e "${GREEN}TinkerPilot has been successfully uninstalled!${NC}"
echo "============================================"
echo ""
