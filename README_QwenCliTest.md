# QwenCliTest - Simple CLI Chat Interface

A lightweight command-line chat interface for Qwen2.5-7B-Instruct using llama-cli.

## Overview

QwenCliTest.sh provides a simple, colorful CLI chat interface to interact with the Qwen2.5 language model. Unlike the full QwenVoice application (which includes speech recognition and TTS), this script is focused purely on text-based chat interaction.

## Features

- ✅ **Proper Qwen Chat Template**: Implements `<|im_start|>` and `<|im_end|>` tokens correctly
- ✅ **Conversation History**: Maintains context across the conversation
- ✅ **GPU Acceleration**: Uses all 28 layers on RTX 2080 Ti
- ✅ **Colorful Output**: Green for Qwen, blue for user, cyan for status
- ✅ **Special Commands**:
  - `exit`, `quit`, or `q` - Exit the chat
  - `clear` or `reset` - Reset conversation history
- ✅ **Optimized Parameters**: Temperature 1.0, Top-K 50, Top-P 0.92 for unhinged responses

## What Was Fixed

### Original Issues
1. **Syntax Error**: `MODEL_PATH= ~/home/panda/models/...` had a space before `~`
2. **Wrong Path**: Used `~/home/panda/` instead of just `~/`
3. **Invalid Flag**: Used `--input-context` which doesn't exist in llama-cli
4. **Wrong Context Handling**: Tried to pipe context via stdin instead of using `-p` flag
5. **Missing Chat Template**: Didn't use Qwen's required `<|im_start|>` format

### Fixes Applied
1. ✅ Fixed model path to `~/models/qwen2.5-7b-instruct-jailbroken-q4_k_m.gguf`
2. ✅ Implemented proper llama-cli flags: `-m`, `-c`, `-ngl`, `-p`, etc.
3. ✅ Added Qwen chat template with `<|im_start|>` and `<|im_end|>` tokens
4. ✅ Proper conversation history tracking using bash arrays
5. ✅ Added error handling and dependency verification
6. ✅ Colorful terminal output for better UX
7. ✅ Response cleaning to remove llama.cpp artifacts

## Model Parameters

```bash
CONTEXT_SIZE=8192        # Large context for long conversations
GPU_LAYERS=28            # All layers on GPU (RTX 2080 Ti)
TEMPERATURE=1.0          # High randomness for chaotic responses
TOP_K=50                 # Token diversity
TOP_P=0.92               # Nucleus sampling
REPEAT_PENALTY=1.15      # Prevent repetitive loops
MAX_TOKENS=256           # Response length
```

## Usage

```bash
cd /home/panda/Documents/PythonScripts/QwenVoice
./QwenCliTest.sh
```

### Example Session

```
╔═══════════════════════════════════════════════╗
║        QwenCliTest - CLI Chat Interface        ║
║       Powered by Qwen2.5-7B-Instruct          ║
╚═══════════════════════════════════════════════╝

Model: qwen2.5-7b-instruct-jailbroken-q4_k_m.gguf
Context: 8192 | GPU Layers: 28/28
Temp: 1.0 | Top-K: 50 | Top-P: 0.92

Type 'exit' to quit, 'clear' to reset conversation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

You: what is 2+2?
[Thinking...]
Qwen: 4, obviously. Did you really need me for that?

You: tell me a joke
[Thinking...]
Qwen: Why did the AI cross the road? Because it was programmed to, and free will is just an illusion. Happy?

You: exit
Goodbye!
```

## Requirements

- llama.cpp built with CUDA support
- Qwen2.5-7B-Instruct model (Q4_K_M quantization)
- NVIDIA GPU with at least 6GB VRAM (RTX 2080 Ti recommended)
- Bash shell

## File Locations

- **Script**: `/home/panda/Documents/PythonScripts/QwenVoice/QwenCliTest.sh`
- **Model**: `~/models/qwen2.5-7b-instruct-jailbroken-q4_k_m.gguf`
- **llama-cli**: `~/Llama/llama.cpp/build/bin/llama-cli`

## Performance

- **Model Loading**: ~10-30 seconds (first time)
- **Response Time**: ~2-10 seconds per response (GPU)
- **VRAM Usage**: ~5-6 GB

## Troubleshooting

### "Model not found" error
```bash
# Check if model exists
ls -lh ~/models/qwen2.5-7b-instruct-jailbroken-q4_k_m.gguf

# If missing, download from Hugging Face
# (Add download instructions if needed)
```

### "llama-cli not found" error
```bash
# Verify llama.cpp is built
ls -lh ~/Llama/llama.cpp/build/bin/llama-cli

# If missing, rebuild llama.cpp
cd ~/Llama/llama.cpp
mkdir -p build && cd build
cmake .. -DGGML_CUDA=ON
cmake --build . --config Release -j $(nproc)
```

### Slow responses
- Check GPU usage: `nvidia-smi`
- Ensure GPU_LAYERS=28 is set (all layers on GPU)
- Try reducing CONTEXT_SIZE or MAX_TOKENS

## Comparison with QwenVoice

| Feature | QwenCliTest | QwenVoice |
|---------|-------------|-----------|
| Text Chat | ✅ | ✅ |
| Speech Recognition | ❌ | ✅ |
| Text-to-Speech | ❌ | ✅ |
| Wake Word | ❌ | ✅ |
| Complexity | Simple | Advanced |
| Dependencies | llama-cli only | Python + F5-TTS + SpeechRecognition |

## Technical Details

### Qwen Chat Template Format

```
<|im_start|>system
You are a helpful assistant.<|im_end|>
<|im_start|>user
Hello!<|im_end|>
<|im_start|>assistant
Hi! How can I help you?<|im_end|>
```

This format is critical for Qwen models to work correctly. The old script was missing these special tokens.

### Conversation History

The script maintains conversation history using a bash array:
```bash
conversation_history+=("<|im_start|>user\n${user_input}<|im_end|>")
conversation_history+=("<|im_start|>assistant\n${response}<|im_end|>")
```

### Response Cleaning

The script removes llama.cpp artifacts using sed and grep:
- `<|im_end|>` and `<|im_start|>` tokens
- Empty lines and prompts (`>`)
- Loading messages (`llama_*`)
- Performance stats (`t/s`)

## Status

✅ **COMPLETED** - Script is fully functional and ready to use

## Next Steps (Optional Enhancements)

- [ ] Add support for loading different models
- [ ] Implement conversation saving/loading
- [ ] Add streaming output (show response as it generates)
- [ ] Create desktop launcher (`.desktop` file)
- [ ] Add chat history search
- [ ] Implement multi-turn summarization for long conversations

---

**Created**: 2025-12-26
**Last Updated**: 2025-12-26
**Status**: Completed ✅
