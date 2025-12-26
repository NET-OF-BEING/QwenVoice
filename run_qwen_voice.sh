#!/bin/bash
# QwenVoice Launcher Script
# Local voice assistant powered by Qwen2.5-7B

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"
PYTHON="$VENV_DIR/bin/python3"
SCRIPT="$SCRIPT_DIR/qwen_voice.py"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}"
echo "╔═══════════════════════════════════════════════╗"
echo "║           QwenVoice - Voice Assistant          ║"
echo "║      Powered by Qwen2.5-7B-Instruct           ║"
echo "╚═══════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if venv exists
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${RED}Error: Virtual environment not found at $VENV_DIR${NC}"
    echo "Please run setup first."
    exit 1
fi

# Check if script exists
if [ ! -f "$SCRIPT" ]; then
    echo -e "${RED}Error: Main script not found at $SCRIPT${NC}"
    exit 1
fi

# Check for model
MODEL_PATH="/home/panda/models/qwen2.5-7b-instruct-jailbroken-q4_k_m.gguf"
if [ ! -f "$MODEL_PATH" ]; then
    echo -e "${RED}Error: Model not found at $MODEL_PATH${NC}"
    exit 1
fi

# Check for llama-cli
LLAMA_CLI="/home/panda/Llama/llama.cpp/build/bin/llama-cli"
if [ ! -f "$LLAMA_CLI" ]; then
    echo -e "${RED}Error: llama-cli not found at $LLAMA_CLI${NC}"
    exit 1
fi

echo -e "${YELLOW}Starting QwenVoice...${NC}"
echo ""

# Suppress ALSA/JACK errors
export AUDIODEV=default
export SDL_AUDIODRIVER=pulseaudio

# Run the assistant
exec "$PYTHON" "$SCRIPT" "$@"
