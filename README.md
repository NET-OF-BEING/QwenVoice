# QwenVoice - Local Voice Assistant

Voice-activated AI assistant powered by Qwen2.5-7B running locally with llama.cpp and F5-TTS.

## Features

- 🎤 **Wake word detection** - "Hey Qwen" to activate
- 🗣️ **Speech recognition** - Google Speech Recognition API
- 🧠 **Local LLM** - Qwen2.5-7B via llama.cpp (GPU accelerated)
- 🔊 **Text-to-speech** - F5-TTS for natural voice synthesis
- 💬 **Conversation history** - Maintains context across exchanges
- 🚫 **No cloud dependencies** - LLM runs entirely on your hardware

## Requirements

### Hardware
- GPU with CUDA support (tested on RTX 2080 Ti)
- 16GB+ RAM
- Microphone

### Software
- Linux (tested on openSUSE)
- Python 3.11+
- CUDA toolkit
- llama.cpp built with CUDA support
- GGUF model file (Qwen2.5-7B-Instruct Q4_K_M)

## Installation

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/QwenVoice.git
cd QwenVoice
```

### 2. Create virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install speechrecognition f5-tts pyaudio
```

### 4. Set up llama.cpp
Build llama.cpp with CUDA support:
```bash
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
mkdir build && cd build
cmake .. -DGGML_CUDA=ON
cmake --build . --config Release
```

Update `LLAMA_CLI` path in `qwen_voice.py`:
```python
LLAMA_CLI = "/path/to/llama.cpp/build/bin/llama-cli"
```

### 5. Download model
Download a Qwen2.5 GGUF model (Q4_K_M recommended):
```bash
# Example - download from Hugging Face
# Place in ~/models/ or update MODEL_PATH in qwen_voice.py
```

Update `MODEL_PATH` in `qwen_voice.py`:
```python
MODEL_PATH = "/path/to/your/model.gguf"
```

## Usage

### Run the assistant
```bash
./run_qwen_voice.sh
```

### Workflow
1. Wait for "Listening for wake word: 'Hey Qwen'"
2. Say "Hey Qwen" to activate
3. Speak your question/command
4. Assistant responds with voice
5. Continue conversation or say "goodbye" to exit

## Configuration

Edit `qwen_voice.py` to customize:

### Model Parameters
```python
CONTEXT_SIZE = 512       # Context window (lower = faster)
GPU_LAYERS = 33          # GPU offload layers (higher = more GPU usage)
MAX_TOKENS = 128         # Response length limit
TEMPERATURE = 1.0        # Creativity (0.1-2.0)
```

### Wake Words
```python
WAKE_WORDS = ["hey qwen", "hey quinn", "hey when"]
```

### System Prompt
Modify the system prompt in `format_prompt()` method to change personality.

## Performance

**Response Times** (RTX 2080 Ti):
- Model loading: ~3-5 seconds
- Speech recognition: ~1-2 seconds
- LLM inference: ~2-5 seconds (512 context, 128 tokens)
- TTS generation: ~1-2 seconds

**Total**: ~7-14 seconds per exchange

## Troubleshooting

### Audio Errors (ALSA/JACK)
Harmless warnings - audio still works. To suppress:
```bash
export AUDIODEV=default
export SDL_AUDIODRIVER=pulseaudio
```

### GPU Not Being Used
Check llama-cli CUDA support:
```bash
/path/to/llama-cli --version
# Should show CUDA devices
```

### Model Too Slow
- Reduce `CONTEXT_SIZE` (512 or 256)
- Reduce `MAX_TOKENS` (64 or 128)
- Use smaller model (1B-3B parameters)
- Increase `GPU_LAYERS` for more GPU offload

### Wake Word Not Detecting
- Speak clearly and distinctly
- Adjust microphone sensitivity
- Check `WAKE_WORDS` list for alternatives

## Architecture

```
User speaks → Speech Recognition (Google) →
  → Text → LLM (llama.cpp + Qwen) → Response Text →
    → TTS (F5-TTS) → Audio playback
```

## Roadmap

- [ ] Convert to llama-server for persistent model loading
- [ ] Add local speech recognition (Whisper)
- [ ] Implement conversation save/load
- [ ] Add command shortcuts (weather, timer, etc.)
- [ ] Multi-language support
- [ ] Custom wake word training

## License

MIT License - see LICENSE file

## Credits

- **Qwen2.5** by Alibaba Cloud
- **llama.cpp** by Georgi Gerganov
- **F5-TTS** by SWivid
- **Speech Recognition** by uberi

## Contributing

Pull requests welcome! Please open an issue first to discuss major changes.

---

**Generated with Claude Code**
