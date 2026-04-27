"""
FRIDAY Voice Module
Handles speech recognition (STT) and text-to-speech (TTS).
"""
import threading
import queue
import os
import tempfile
import config

# TTS Engine
try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    print(f"[{config.ASSISTANT_NAME}] pyttsx3 not installed. TTS disabled.")

# STT Engine
try:
    import speech_recognition as sr
    STT_AVAILABLE = True
except ImportError:
    STT_AVAILABLE = False
    print(f"[{config.ASSISTANT_NAME}] SpeechRecognition not installed. STT disabled.")


class RavenVoice:
    """Voice input/output manager for FRIDAY."""

    def __init__(self):
        self.tts_engine = None
        self.recognizer = None
        self.microphone = None
        self.is_listening = False
        self.is_speaking = False
        self.speech_queue = queue.Queue()
        self._init_tts()
        self._init_stt()
        self._start_speech_worker()

    def _init_tts(self):
        """Initialize text-to-speech engine."""
        if not TTS_AVAILABLE:
            return

        try:
            self.tts_engine = pyttsx3.init()
            voices = self.tts_engine.getProperty('voices')

            # Try to select the configured voice
            if config.VOICE_INDEX < len(voices):
                self.tts_engine.setProperty('voice', voices[config.VOICE_INDEX].id)
            elif len(voices) > 0:
                self.tts_engine.setProperty('voice', voices[0].id)

            self.tts_engine.setProperty('rate', config.VOICE_RATE)
            self.tts_engine.setProperty('volume', config.VOICE_VOLUME)
            print(f"[{config.ASSISTANT_NAME}] TTS engine initialized.")
        except Exception as e:
            print(f"[{config.ASSISTANT_NAME}] TTS init error: {e}")
            self.tts_engine = None

    def _init_stt(self):
        """Initialize speech recognition."""
        if not STT_AVAILABLE:
            return

        try:
            self.recognizer = sr.Recognizer()
            self.recognizer.energy_threshold = 300
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.pause_threshold = 1.0
            print(f"[{config.ASSISTANT_NAME}] STT engine initialized.")
        except Exception as e:
            print(f"[{config.ASSISTANT_NAME}] STT init error: {e}")

    def _start_speech_worker(self):
        """Start background thread for TTS to avoid blocking."""
        def worker():
            while True:
                text = self.speech_queue.get()
                if text is None:
                    break
                self._speak_sync(text)
                self.speech_queue.task_done()

        self.speech_thread = threading.Thread(target=worker, daemon=True)
        self.speech_thread.start()

    def _speak_sync(self, text: str):
        """Synchronously speak text (runs in worker thread)."""
        if not self.tts_engine:
            return

        try:
            self.is_speaking = True
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except Exception as e:
            print(f"[{config.ASSISTANT_NAME}] Speech error: {e}")
        finally:
            self.is_speaking = False

    def speak(self, text: str):
        """Queue text for speech output (non-blocking)."""
        if TTS_AVAILABLE and self.tts_engine:
            self.speech_queue.put(text)
        print(f"[{config.ASSISTANT_NAME}] 🔊 {text}")

    def listen(self, timeout: int = 5, phrase_time_limit: int = 15) -> str:
        """
        Listen for voice input and return transcribed text.

        Args:
            timeout: Max seconds to wait for speech to start
            phrase_time_limit: Max seconds for the entire phrase

        Returns:
            Transcribed text or empty string on failure
        """
        if not STT_AVAILABLE or not self.recognizer:
            return ""

        try:
            self.is_listening = True
            with sr.Microphone() as source:
                print(f"[{config.ASSISTANT_NAME}] 🎤 Listening...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit
                )

            print(f"[{config.ASSISTANT_NAME}] 🔄 Processing speech...")

            # Try Groq Whisper API first for better accuracy
            if config.GROQ_API_KEY and config.GROQ_API_KEY != "your_groq_api_key_here":
                try:
                    return self._transcribe_groq(audio)
                except Exception:
                    pass

            # Fallback to Google Web Speech API (free, no key needed)
            try:
                text = self.recognizer.recognize_google(audio)
                print(f"[{config.ASSISTANT_NAME}] 📝 Heard: {text}")
                return text
            except sr.UnknownValueError:
                print(f"[{config.ASSISTANT_NAME}] Could not understand audio")
                return ""
            except sr.RequestError as e:
                print(f"[{config.ASSISTANT_NAME}] Speech API error: {e}")
                return ""

        except sr.WaitTimeoutError:
            print(f"[{config.ASSISTANT_NAME}] No speech detected")
            return ""
        except Exception as e:
            print(f"[{config.ASSISTANT_NAME}] Listen error: {e}")
            return ""
        finally:
            self.is_listening = False

    def _transcribe_groq(self, audio) -> str:
        """Transcribe audio using Groq's Whisper API."""
        from groq import Groq

        # Save audio to temp file
        wav_data = audio.get_wav_data()
        temp_path = os.path.join(config.TEMP_DIR, "input_audio.wav")
        with open(temp_path, "wb") as f:
            f.write(wav_data)

        client = Groq(api_key=config.GROQ_API_KEY)
        with open(temp_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model=config.GROQ_WHISPER_MODEL,
                file=audio_file,
                response_format="text"
            )

        text = transcription.strip()
        print(f"[{config.ASSISTANT_NAME}] 📝 Heard (Whisper): {text}")
        return text

    def detect_wake_word(self, text: str) -> bool:
        """Check if the wake word is in the spoken text."""
        return config.WAKE_WORD.lower() in text.lower()

    def shutdown(self):
        """Clean up voice resources."""
        self.speech_queue.put(None)
        if self.tts_engine:
            try:
                self.tts_engine.stop()
            except Exception:
                pass
