#!/bin/bash
# QwenCliTest - Simple CLI chat with Qwen2.5 via llama-cli
# Usage: ./QwenCliTest.sh

# Configuration
LLAMA_CLI=~/Llama/llama.cpp/build/bin/llama-cli
MODEL_PATH=~/models/qwen2.5-7b-instruct-q4_k_m.gguf  # Using regular model (non-jailbroken for better performance)

# Model parameters
CONTEXT_SIZE=2048      # Reduced from 8192 for faster initialization
GPU_LAYERS=28
TEMPERATURE=1.0
TOP_K=50
TOP_P=0.92
REPEAT_PENALTY=1.15
MAX_TOKENS=256

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

# Verify dependencies
if [ ! -f "$LLAMA_CLI" ]; then
    echo -e "${RED}Error: llama-cli not found at $LLAMA_CLI${NC}"
    exit 1
fi

if [ ! -f "$MODEL_PATH" ]; then
    echo -e "${RED}Error: Model not found at $MODEL_PATH${NC}"
    exit 1
fi

# Initialize conversation history
declare -a conversation_history=()

# Function to build prompt with Qwen chat template
build_prompt() {
    local user_input="$1"
    local prompt=""

    # System message
    prompt+="<|im_start|>system
You are a helpful AI assistant. Be concise and conversational. No markdown or formatting - just plain text since this is CLI output.<|im_end|>
"

    # Add conversation history
    for entry in "${conversation_history[@]}"; do
        prompt+="$entry
"
    done

    # Add current user message
    prompt+="<|im_start|>user
${user_input}<|im_end|>
<|im_start|>assistant
"

    echo "$prompt"
}

# Function to query the LLM
ask_llm() {
    local user_input="$1"

    # Add user message to history
    conversation_history+=("<|im_start|>user
${user_input}<|im_end|>")

    # Build full prompt
    local prompt=$(build_prompt "$user_input")

    echo -e "${CYAN}[Thinking...]${NC}"

    # Query llama-cli with proper flags
    # --single-turn: Exit after one response (non-interactive)
    local raw_output=$("$LLAMA_CLI" \
        -m "$MODEL_PATH" \
        -c "$CONTEXT_SIZE" \
        -ngl "$GPU_LAYERS" \
        --temp "$TEMPERATURE" \
        --top-p "$TOP_P" \
        --top-k "$TOP_K" \
        --repeat-penalty "$REPEAT_PENALTY" \
        -n "$MAX_TOKENS" \
        --single-turn \
        --no-display-prompt \
        --log-disable \
        -p "$prompt" \
        2>&1)

    # Extract response - it starts with "|" but has backspace control chars
    # 1. Strip backspaces, 2. Filter debug lines, 3. Extract response line, 4. Clean
    local response=$(echo "$raw_output" | \
        tr -d '\010\015' | \
        sed 's/llama_memory.*//' | \
        sed 's/~llama.*//' | \
        sed 's/\[ Prompt:.*//' | \
        sed 's/Exiting.*//' | \
        grep "^|" | \
        grep -v "memory breakdown" | \
        grep -v "total" | \
        sed 's/^|[[:space:]]*//' | \
        sed 's/<|im_end|>.*//' | \
        sed 's/<|im_start|>.*//' | \
        sed 's/  */ /g' | \
        sed 's/^ *//' | \
        sed 's/ *$//')

    # Add assistant response to history
    if [ -n "$response" ]; then
        conversation_history+=("<|im_start|>assistant
${response}<|im_end|>")

        # Display response
        echo -e "${BOLD}${GREEN}Qwen:${NC} ${response}"
    else
        echo -e "${RED}Error: No response generated${NC}"
    fi
}

# Print header
echo -e "${GREEN}"
echo "╔═══════════════════════════════════════════════╗"
echo "║        QwenCliTest - CLI Chat Interface        ║"
echo "║       Powered by Qwen2.5-7B-Instruct          ║"
echo "╚═══════════════════════════════════════════════╝"
echo -e "${NC}"
echo -e "${YELLOW}Model:${NC} $(basename "$MODEL_PATH")"
echo -e "${YELLOW}Context:${NC} $CONTEXT_SIZE | ${YELLOW}GPU Layers:${NC} $GPU_LAYERS/28"
echo -e "${YELLOW}Temp:${NC} $TEMPERATURE | ${YELLOW}Top-K:${NC} $TOP_K | ${YELLOW}Top-P:${NC} $TOP_P"
echo ""
echo -e "${CYAN}Type 'exit' to quit, 'clear' to reset conversation${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Main conversation loop
while true; do
    # Read user input
    echo -ne "${BOLD}${BLUE}You:${NC} "
    read -r user_input

    # Handle special commands
    case "$user_input" in
        exit|quit|q)
            echo -e "${GREEN}Goodbye!${NC}"
            exit 0
            ;;
        clear|reset)
            conversation_history=()
            echo -e "${YELLOW}Conversation cleared.${NC}"
            continue
            ;;
        "")
            continue
            ;;
    esac

    # Query the LLM
    ask_llm "$user_input"
    echo ""
done
