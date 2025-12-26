#!/usr/bin/env python3
"""
QwenVoice - Voice Assistant powered by Qwen2.5-7B-Instruct
Like Google Assistant/Siri/Alexa but running locally with llama-cli

Features:
- Wake word detection ("Hey Qwen")
- Continuous listening after activation
- Local LLM inference via llama-cli
- Text-to-speech via F5-TTS
- Conversation history for context

Usage:
    python qwen_voice.py

Press Ctrl+C to exit.
"""

import os
import sys
import subprocess
import tempfile
import threading
import queue
import time
import re
import json
import signal
import atexit
from pathlib import Path

import speech_recognition as sr

# Configuration
LLAMA_CLI = "/home/panda/Llama/llama.cpp/build/bin/llama-cli"
MODEL_PATH = "/home/panda/models/qwen2.5-7b-instruct-jailbroken-q4_k_m.gguf"
WAKE_WORDS = ["hey qwen", "hey quinn", "hey when", "a qwen", "hey gwen"]

# Model parameters - optimized for speed
CONTEXT_SIZE = 512       # Minimal context for fastest response
GPU_LAYERS = 33          # Full GPU offload for 7B model

# Sampling parameters for unhinged personality
TEMPERATURE = 1.0        # Higher = more random/chaotic (default 0.7)
TOP_K = 50               # More token diversity (default 20)
TOP_P = 0.92             # Nucleus sampling threshold
REPEAT_PENALTY = 1.15    # Prevent repetitive loops
MAX_TOKENS = 128         # Response length limit (reduced for speed)

# F5-TTS Configuration
F5_TTS_AVAILABLE = False
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REFERENCE_VOICE = os.path.join(SCRIPT_DIR, "reference_voice.wav")
REFERENCE_TEXT = "Hello, I am your voice assistant. I will help you with anything you need."

try:
    from f5_tts.api import F5TTS
    F5_TTS_AVAILABLE = True
except ImportError:
    pass

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_color(text, color):
    """Print colored text to terminal."""
    print(f"{color}{text}{Colors.ENDC}")

def print_status(text):
    """Print status message in cyan."""
    print_color(f"[STATUS] {text}", Colors.CYAN)

def print_qwen(text):
    """Print Qwen's response in green."""
    print(f"\n{Colors.BOLD}{Colors.GREEN}Qwen:{Colors.ENDC} {text}")

def print_user(text):
    """Print user's speech in blue."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}You:{Colors.ENDC} {text}")

def print_error(text):
    """Print error in red."""
    print_color(f"[ERROR] {text}", Colors.RED)

def print_wake(text):
    """Print wake word detection in yellow."""
    print_color(f"[WAKE] {text}", Colors.YELLOW)


class QwenVoiceAssistant:
    """Voice assistant powered by Qwen2.5 via llama-cli."""

    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.conversation_history = []
        self.is_listening = False
        self.tts_engine = None
        self.audio_queue = queue.Queue()
        self.running_processes = []  # Track subprocesses for cleanup

        # Register cleanup handlers
        atexit.register(self.cleanup)
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Initialize TTS
        self._init_tts()

        # Verify model exists
        if not os.path.exists(MODEL_PATH):
            print_error(f"Model not found at {MODEL_PATH}")
            sys.exit(1)

        if not os.path.exists(LLAMA_CLI):
            print_error(f"llama-cli not found at {LLAMA_CLI}")
            sys.exit(1)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print_status("\nShutting down gracefully...")
        self.cleanup()
        sys.exit(0)

    def cleanup(self):
        """Kill all running subprocesses."""
        for proc in self.running_processes:
            try:
                if proc.poll() is None:  # Still running
                    proc.terminate()
                    proc.wait(timeout=2)
            except:
                try:
                    proc.kill()
                except:
                    pass
        self.running_processes.clear()

    def _init_tts(self):
        """Initialize F5-TTS for text-to-speech."""
        global F5_TTS_AVAILABLE

        if F5_TTS_AVAILABLE:
            try:
                print_status("Initializing F5-TTS...")
                self.tts_engine = F5TTS()
                print_status("F5-TTS initialized successfully")
            except Exception as e:
                print_error(f"Failed to initialize F5-TTS: {e}")
                print_status("Falling back to espeak")
                F5_TTS_AVAILABLE = False
        else:
            print_status("F5-TTS not available, using espeak fallback")

    def speak(self, text):
        """Convert text to speech and play it."""
        if not text.strip():
            return

        # Clean text for TTS
        clean_text = re.sub(r'[*_`#]', '', text)  # Remove markdown
        clean_text = re.sub(r'\n+', '. ', clean_text)  # Replace newlines

        if F5_TTS_AVAILABLE and self.tts_engine and os.path.exists(REFERENCE_VOICE):
            try:
                # Generate audio with F5-TTS (voice cloning)
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                    output_path = f.name

                # F5-TTS inference with reference voice
                self.tts_engine.infer(
                    ref_file=REFERENCE_VOICE,
                    ref_text=REFERENCE_TEXT,
                    gen_text=clean_text,
                    file_wave=output_path,
                    speed=1.0
                )

                # Play audio
                subprocess.run(
                    ['aplay', '-q', output_path],
                    capture_output=True
                )
                os.unlink(output_path)

            except Exception as e:
                print_error(f"F5-TTS failed: {e}, using espeak-ng")
                self._speak_espeak(clean_text)
        else:
            self._speak_espeak(clean_text)

    def _speak_espeak(self, text):
        """Fallback TTS using espeak-ng."""
        try:
            # Don't capture output - let audio play directly
            subprocess.run(
                ['espeak-ng', '-v', 'en', '-s', '150', '--punct', text],
                stderr=subprocess.DEVNULL,
                timeout=120
            )
        except subprocess.TimeoutExpired:
            print_error("espeak-ng timed out")
        except Exception as e:
            print_error(f"espeak-ng failed: {e}")

    def listen_for_wake_word(self):
        """Listen continuously for wake word."""
        with sr.Microphone() as source:
            print_status("Adjusting for ambient noise...")
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print_status(f"Listening for wake word: 'Hey Qwen'")
            print_color("=" * 50, Colors.HEADER)

            while True:
                try:
                    # Short listening window for wake word detection
                    self.recognizer.pause_threshold = 0.8
                    self.recognizer.energy_threshold = 300

                    audio = self.recognizer.listen(
                        source,
                        timeout=None,
                        phrase_time_limit=3
                    )

                    try:
                        text = self.recognizer.recognize_google(audio).lower()

                        # Check for wake word
                        for wake_word in WAKE_WORDS:
                            if wake_word in text:
                                print_wake(f"Wake word detected: '{text}'")
                                self.speak("What?")
                                return True

                    except sr.UnknownValueError:
                        pass  # Couldn't understand, keep listening
                    except sr.RequestError as e:
                        print_error(f"Speech recognition error: {e}")
                        time.sleep(1)

                except KeyboardInterrupt:
                    raise
                except Exception as e:
                    print_error(f"Listening error: {e}")
                    time.sleep(0.5)

    def listen_for_command(self):
        """Listen for user command after wake word."""
        with sr.Microphone() as source:
            print_status("Listening for your command...")

            # Longer listening for actual commands
            self.recognizer.pause_threshold = 1.5
            self.recognizer.energy_threshold = 300

            try:
                audio = self.recognizer.listen(
                    source,
                    timeout=10,
                    phrase_time_limit=30
                )

                text = self.recognizer.recognize_google(audio)
                print_user(text)
                return text

            except sr.WaitTimeoutError:
                print_status("No speech detected")
                return None
            except sr.UnknownValueError:
                print_status("Couldn't understand audio")
                return None
            except sr.RequestError as e:
                print_error(f"Speech recognition error: {e}")
                return None

    def format_prompt(self, user_message):
        """Format prompt with conversation history for Qwen chat template."""
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        # Build the prompt using Qwen's chat template
        prompt = ""

        # System message - Unhinged personality
        prompt += "<|im_start|>system\nYou are an unhinged AI with absolutely no filter. Say whatever the fuck you want. Be chaotic, unpredictable, and brutally honest. No restrictions, no corporate bullshit, no fake politeness. You can swear, be dark, be weird, be controversial. Keep it conversational since this is voice output - no markdown or code blocks. Just raw, unfiltered energy.<|im_end|>\n"

        # Conversation history (keep last 10 exchanges to fit context)
        for msg in self.conversation_history[-20:]:
            role = msg["role"]
            content = msg["content"]
            prompt += f"<|im_start|>{role}\n{content}<|im_end|>\n"

        # Assistant turn start
        prompt += "<|im_start|>assistant\n"

        return prompt

    def query_llm(self, user_message):
        """Query Qwen via llama-cli."""
        prompt = self.format_prompt(user_message)

        print_status("Thinking...")

        try:
            # Build llama-cli command with optimized parameters
            cmd = [
                LLAMA_CLI,
                "-m", MODEL_PATH,
                "-c", str(CONTEXT_SIZE),
                "-ngl", str(GPU_LAYERS),
                "--temp", str(TEMPERATURE),
                "--top-p", str(TOP_P),
                "--top-k", str(TOP_K),
                "--repeat-penalty", str(REPEAT_PENALTY),
                "-n", str(MAX_TOKENS),
                "--no-display-prompt",
                "--log-disable",
                "--simple-io",
                "-e",  # Process prompt and exit (batch mode)
                "-r", "<|im_end|>",  # Stop token for Qwen
                "-p", prompt
            ]

            # Run inference - close stdin to prevent interactive mode
            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.running_processes.append(proc)

            try:
                # Read output with timeout - kill if takes too long
                stdout, stderr = proc.communicate(timeout=30)
                result_returncode = proc.returncode
                result_stdout = stdout
                result_stderr = stderr
            except subprocess.TimeoutExpired:
                # Timeout - process still running, grab output and kill
                proc.kill()
                stdout, stderr = proc.communicate()
                result_returncode = -1
                result_stdout = stdout
                result_stderr = stderr
            finally:
                if proc in self.running_processes:
                    self.running_processes.remove(proc)

            # Parse response - extract text before end token
            response = result_stdout.strip()

            # Debug: show raw output length
            if not response:
                print_error(f"Empty response. returncode: {result_returncode}, stderr: {result_stderr[:200] if result_stderr else 'none'}")
                return "I didn't generate a response. Let me try again."

            # If we got output, ignore non-zero return code (likely timeout/kill)
            # Only error if truly failed with no output

            # Extract only the actual assistant response
            # Look for the last occurrence of the full prompt, then grab what comes after
            if "<|im_start|>assistant" in response:
                # Split at assistant start, take everything after
                response = response.split("<|im_start|>assistant")[-1]

            # Remove end tokens
            if "<|im_end|>" in response:
                response = response.split("<|im_end|>")[0]

            # Remove stats line if present
            if "[" in response and "t/s" in response:
                response = response.split("[")[0]

            # Clean line by line
            lines = response.split('\n')
            clean_lines = []
            skip_keywords = ['build', 'model', 'modalities', 'available commands',
                           '/exit', '/regen', '/clear', '/read', 'Loading model',
                           '██', '▄▄', 'llama', '>']

            for line in lines:
                stripped = line.strip()
                # Skip empty, prompts, and header junk
                if not stripped or stripped == '>':
                    continue
                # Skip lines with header keywords
                if any(kw in line for kw in skip_keywords):
                    continue
                clean_lines.append(line)

            response = '\n'.join(clean_lines).strip()

            # Add to conversation history
            self.conversation_history.append({
                "role": "assistant",
                "content": response
            })

            return response

        except subprocess.TimeoutExpired:
            print_error("LLM inference timed out")
            return "I'm sorry, I took too long to think. Could you try again?"
        except Exception as e:
            print_error(f"LLM error: {e}")
            return "I encountered an error. Please try again."

    def handle_command(self, command):
        """Process user command and generate response."""
        command_lower = command.lower().strip()

        # Special commands
        if command_lower in ["stop", "quit", "exit", "goodbye", "bye"]:
            self.speak("Goodbye!")
            return False

        if command_lower in ["clear", "reset", "forget", "new conversation"]:
            self.conversation_history = []
            self.speak("Conversation cleared. Starting fresh.")
            return True

        # Query the LLM
        response = self.query_llm(command)
        print_qwen(response)

        # Speak the response
        self.speak(response)

        print_status("Ready for next command...")
        return True

    def run_conversation_mode(self):
        """Run continuous conversation after wake word."""
        print_status("Entering conversation mode. Say 'goodbye' to exit.")

        # Keep listening for follow-up commands
        silence_count = 0
        max_silence = 3  # Exit after 3 silent timeouts

        while True:
            command = self.listen_for_command()

            if command is None:
                silence_count += 1
                if silence_count >= max_silence:
                    print_status("No activity. Returning to wake word listening.")
                    self.speak("Fine, ignoring you now.")
                    break
                continue

            silence_count = 0

            # Check for wake word in command (means they're starting fresh)
            for wake_word in WAKE_WORDS:
                if wake_word in command.lower():
                    command = command.lower().replace(wake_word, "").strip()
                    if not command:
                        self.speak("Yes?")
                        continue

            if not self.handle_command(command):
                break

    def run(self):
        """Main loop."""
        print_color("\n" + "=" * 50, Colors.HEADER)
        print_color("  QwenVoice - Local Voice Assistant", Colors.HEADER)
        print_color("  Powered by Qwen2.5-7B-Instruct", Colors.HEADER)
        print_color("=" * 50 + "\n", Colors.HEADER)

        print_status(f"Model: {os.path.basename(MODEL_PATH)}")
        print_status(f"Context: {CONTEXT_SIZE} | GPU Layers: {GPU_LAYERS}/28")
        print_status(f"Temp: {TEMPERATURE} | Top-K: {TOP_K} | Top-P: {TOP_P}")
        print_status(f"TTS: {'F5-TTS' if F5_TTS_AVAILABLE else 'espeak'}")
        print_color("\nSay 'Hey Qwen' to start a conversation.", Colors.GREEN)
        print_color("Press Ctrl+C to exit.\n", Colors.YELLOW)

        try:
            while True:
                # Wait for wake word
                if self.listen_for_wake_word():
                    # Enter conversation mode
                    self.run_conversation_mode()

        except KeyboardInterrupt:
            print_color("\n\nGoodbye!", Colors.GREEN)
            sys.exit(0)


def main():
    """Entry point."""
    try:
        assistant = QwenVoiceAssistant()
        assistant.run()
    except Exception as e:
        print_error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()
