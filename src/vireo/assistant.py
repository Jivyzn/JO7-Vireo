"""Offline voice assistant for JØ7 VIREO.

The assistant combines Vosk speech recognition, local TTS, optional Ollama
fallback, and timed Hailo object-detection sessions.  It is derived from the
working ``MainFinal.py`` prototype and removes machine-specific paths.
"""

from __future__ import annotations

import hashlib
import json
import os
import queue
import re
import shutil
import signal
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .config import AssistantConfig

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.?!])\s+")

CITY_TIMEZONES = {
    "cape town": "Africa/Johannesburg",
    "durban": "Africa/Johannesburg",
    "johannesburg": "Africa/Johannesburg",
    "richards bay": "Africa/Johannesburg",
    "lagos": "Africa/Lagos",
    "nairobi": "Africa/Nairobi",
    "casablanca": "Africa/Casablanca",
    "tokyo": "Asia/Tokyo",
    "new york": "America/New_York",
    "london": "Europe/London",
}

INTENT_COOLDOWNS = {
    "object_detection": 20.0,
    "fire": 10.0,
    "water": 10.0,
    "where_am_i": 4.0,
    "time": 2.0,
    "date": 2.0,
    "default": 2.0,
}

OBJECT_DETECTION_PHRASES = (
    "what objects are around me",
    "what's in front of me",
    "what objects are near me",
    "what's nearby",
    "describe surroundings",
)


def split_text_into_chunks(text: str, max_chars: int = 220) -> list[str]:
    """Split text at sentence boundaries for responsive local TTS."""

    sentences = _SENTENCE_SPLIT_RE.split(text.strip())
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        if not sentence.strip():
            continue
        candidate = f"{current} {sentence}".strip() if current else sentence
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                chunks.append(current)
            current = sentence
    if current:
        chunks.append(current)
    if not chunks and text:
        chunks = [text[index : index + max_chars] for index in range(0, len(text), max_chars)]
    return chunks


def get_world_time(city: str) -> str:
    timezone_name = CITY_TIMEZONES.get(city.lower().strip())
    if not timezone_name:
        return f"Sorry, I do not have offline time-zone information for {city}."
    now = datetime.now(ZoneInfo(timezone_name))
    return f"The time in {city.title()} is {now.strftime('%I:%M %p')}."


def response_for_phrase(phrase: str, config: AssistantConfig) -> str:
    """Return a dynamic or fixed response for a recognised phrase."""

    now = datetime.now()
    fixed = {
        "how to make a fire": (
            "Gather dry tinder, small kindling, and larger fuel. Clear a safe area, "
            "light the tinder, add fuel gradually, never leave the fire unattended, "
            "and extinguish it completely."
        ),
        "how do i filter water": (
            "Choose flowing water if possible, strain visible particles through clean cloth, "
            "and then boil the water or use a certified purification method before drinking."
        ),
        "help": (
            "You can ask what is around you, request the time or date, ask where you are, "
            "say repeat that, or say stop to interrupt speech."
        ),
        "increase volume": "Increasing the volume is not yet connected to system audio controls.",
        "decrease volume": "Decreasing the volume is not yet connected to system audio controls.",
        "battery level": "Battery telemetry is not currently available.",
        "tell me a joke": "Why did the scarecrow win an award? Because he was outstanding in his field.",
        "what's temperature": "Temperature information is not currently available.",
        "what's the weather": "Weather information is unavailable because VIREO operates offline.",
        "read notifications": "Notification integration is not currently configured.",
        "how do i navigate": (
            "Ask what objects are around you, continue using your cane or trained mobility aid, "
            "and request human assistance whenever conditions are uncertain."
        ),
        "call for help": (
            "Emergency calling is not currently connected. Use your phone or a configured "
            "emergency button to contact assistance."
        ),
        "thank you": "You are most welcome.",
        "thanks": "You are most welcome.",
    }

    if phrase in {"read me the date", "what's the date", "what is the date"}:
        return "Today's date is " + now.strftime("%A, %B %d, %Y") + "."
    if phrase in {"what time is it", "what's the time", "what is the time"}:
        return "The local time is " + now.strftime("%I:%M %p") + "."
    if phrase == "where am i":
        if config.configured_location:
            return f"Your configured location is {config.configured_location}."
        return "Location is not configured. Set VIREO_LOCATION before starting the assistant."
    if phrase in OBJECT_DETECTION_PHRASES:
        return "Starting object detection."
    if phrase == "list available commands":
        return (
            "You can say where am I, what objects are around me, what is the time, "
            "what is the date, repeat that, help, or stop."
        )
    return fixed.get(phrase, "")


class IntentThrottle:
    def __init__(self) -> None:
        self._last_time: dict[str, float] = {}
        self._lock = threading.Lock()

    def allowed(self, key: str) -> bool:
        now = time.monotonic()
        cooldown = INTENT_COOLDOWNS.get(key, INTENT_COOLDOWNS["default"])
        with self._lock:
            last = self._last_time.get(key, 0.0)
            if now - last >= cooldown:
                self._last_time[key] = now
                return True
        return False


class LocalSpeechEngine:
    """Generate WAV files using Coqui TTS or an eSpeak fallback."""

    def __init__(self, config: AssistantConfig) -> None:
        self.config = config
        self.coqui = None
        self.espeak = shutil.which("espeak-ng") or shutil.which("espeak")
        requested = config.tts_engine

        if requested not in {"auto", "coqui", "espeak"}:
            raise ValueError("VIREO_TTS_ENGINE must be auto, coqui, or espeak")

        if requested in {"auto", "coqui"}:
            try:
                from TTS.api import TTS

                self.coqui = TTS(
                    model_name=config.tts_model,
                    progress_bar=False,
                    gpu=False,
                )
                print(f"Loaded Coqui TTS model: {config.tts_model}")
            except Exception as exc:
                if requested == "coqui":
                    raise RuntimeError(f"Could not load Coqui TTS: {exc}") from exc
                print(f"[TTS] Coqui unavailable; using eSpeak fallback: {exc}")

        if self.coqui is None and not self.espeak:
            raise RuntimeError("No local TTS engine found. Install Coqui TTS or espeak-ng.")

    def synthesise(self, text: str, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(".tmp.wav")
        if self.coqui is not None:
            self.coqui.tts_to_file(
                text=text,
                speaker=self.config.speaker,
                file_path=str(temporary),
            )
        else:
            subprocess.run(
                [self.espeak, "-w", str(temporary), text],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        temporary.replace(destination)


class AccessibleAssistant:
    def __init__(self, config: AssistantConfig) -> None:
        self.config = config
        self.stop_event = threading.Event()
        self.playing_event = threading.Event()
        self.mode = "idle"
        self.mode_lock = threading.Lock()
        self.last_spoken_text = ""
        self.throttle = IntentThrottle()

        self.mic_queue: queue.Queue[bytes] = queue.Queue(maxsize=64)
        self.synthesis_queue: queue.Queue[tuple[str, int] | None] = queue.Queue()
        self.play_queue: queue.Queue[Path | None] = queue.Queue()
        self.ollama_queue: queue.Queue[tuple[str, int] | None] = queue.Queue()
        self.ollama_responses: queue.Queue[tuple[int, str]] = queue.Queue()

        self.config.audio_cache_dir.mkdir(parents=True, exist_ok=True)
        self._validate_paths()

        try:
            import sounddevice as sd
            import soundfile as sf
            import vosk
        except ImportError as exc:
            raise RuntimeError(f"Missing assistant dependency: {exc}") from exc

        self.sd = sd
        self.sf = sf
        self.vosk = vosk
        self.vosk_model = vosk.Model(str(config.vosk_model_path))
        self.recognizer = vosk.KaldiRecognizer(self.vosk_model, config.sample_rate)
        self.speech_engine = LocalSpeechEngine(config)

        self.threads = [
            threading.Thread(target=self._synthesis_worker, name="tts-synthesis", daemon=True),
            threading.Thread(target=self._playback_worker, name="tts-playback", daemon=True),
            threading.Thread(target=self._ollama_worker, name="ollama-worker", daemon=True),
        ]

    def _validate_paths(self) -> None:
        required = {
            "Vosk model": self.config.vosk_model_path,
            "object-detection launcher": self.config.detection_script,
            "HEF model": self.config.hef_model_path,
        }
        missing = [f"{name}: {path}" for name, path in required.items() if not path.exists()]
        if missing:
            raise FileNotFoundError("Missing required VIREO files:\n- " + "\n- ".join(missing))

    def _cache_path(self, text: str, index: int) -> Path:
        digest = hashlib.sha1(f"{text}::{index}".encode("utf-8")).hexdigest()
        return self.config.audio_cache_dir / f"{digest}.wav"

    def _synthesis_worker(self) -> None:
        while not self.stop_event.is_set():
            item = self.synthesis_queue.get()
            try:
                if item is None:
                    return
                chunk, index = item
                destination = self._cache_path(chunk, index)
                if not destination.exists():
                    try:
                        self.speech_engine.synthesise(chunk, destination)
                    except Exception as exc:
                        print(f"[TTS synthesis error] {exc}")
                        continue
                self.play_queue.put(destination)
            finally:
                self.synthesis_queue.task_done()

    def _playback_worker(self) -> None:
        while not self.stop_event.is_set():
            item = self.play_queue.get()
            try:
                if item is None:
                    return
                if not item.exists():
                    continue
                self.playing_event.set()
                data, sample_rate = self.sf.read(str(item), dtype="float32")
                self.sd.play(data, sample_rate, blocking=True)
            except Exception as exc:
                print(f"[Playback error] {exc}")
            finally:
                self.playing_event.clear()
                with self.mode_lock:
                    if self.mode == "speaking" and self.play_queue.empty():
                        self.mode = "idle"
                self.play_queue.task_done()

    def _ollama_worker(self) -> None:
        if not shutil.which("ollama"):
            print("[Ollama] executable not found; free-form fallback is disabled.")
        while not self.stop_event.is_set():
            item = self.ollama_queue.get()
            try:
                if item is None:
                    return
                prompt, request_id = item
                if not shutil.which("ollama"):
                    response = "That command is not available in the offline command set."
                else:
                    try:
                        result = subprocess.run(
                            ["ollama", "run", self.config.ollama_model],
                            input=prompt,
                            capture_output=True,
                            text=True,
                            check=False,
                            timeout=self.config.ollama_timeout,
                        )
                        lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
                        response = lines[-1] if lines else "The local language model returned no answer."
                        response = response[: self.config.max_ollama_chars]
                    except subprocess.TimeoutExpired:
                        response = "The local language model timed out."
                    except Exception as exc:
                        response = f"The local language model failed: {exc}"
                self.ollama_responses.put((request_id, response))
            finally:
                self.ollama_queue.task_done()

    def _audio_callback(self, input_data, _frames, _time_info, status) -> None:
        if status:
            print(f"[Microphone] {status}")
        payload = bytes(input_data)
        try:
            self.mic_queue.put_nowait(payload)
        except queue.Full:
            try:
                self.mic_queue.get_nowait()
                self.mic_queue.task_done()
            except queue.Empty:
                pass
            try:
                self.mic_queue.put_nowait(payload)
            except queue.Full:
                pass

    def speak(self, text: str) -> None:
        if not text:
            return
        self.last_spoken_text = text
        with self.mode_lock:
            self.mode = "speaking"
        for index, chunk in enumerate(split_text_into_chunks(text, max_chars=240)):
            cached = self._cache_path(chunk, index)
            if cached.exists():
                self.play_queue.put(cached)
            else:
                self.synthesis_queue.put((chunk, index))

    def say_and_log(self, text: str) -> None:
        print(text)
        self.speak(text)

    def _precache(self) -> None:
        phrases = [
            "Assistant ready. Say help to list commands.",
            response_for_phrase("help", self.config),
            response_for_phrase("where am i", self.config),
        ]
        for text in phrases:
            for index, chunk in enumerate(split_text_into_chunks(text)):
                destination = self._cache_path(chunk, index)
                if destination.exists():
                    continue
                try:
                    self.speech_engine.synthesise(chunk, destination)
                except Exception as exc:
                    print(f"[Precache error] {exc}")

    def _start_detection(self) -> None:
        def runner() -> None:
            with self.mode_lock:
                self.mode = "object_detection"
            environment = os.environ.copy()
            environment["VIREO_HEF_MODEL"] = str(self.config.hef_model_path)
            environment["VIREO_DETECTION_SECONDS"] = str(self.config.detection_seconds)
            try:
                subprocess.run(
                    [str(self.config.detection_script)],
                    check=False,
                    env=environment,
                )
            except Exception as exc:
                print(f"[Object detection error] {exc}")
            finally:
                time.sleep(0.35)
                with self.mode_lock:
                    self.mode = "idle"

        threading.Thread(target=runner, name="object-detection", daemon=True).start()

    def _interrupt_speech(self) -> None:
        try:
            self.sd.stop()
        except Exception:
            pass
        while True:
            try:
                self.play_queue.get_nowait()
                self.play_queue.task_done()
            except queue.Empty:
                break
        with self.mode_lock:
            self.mode = "idle"

    def _handle_command(self, command: str) -> bool:
        if command in {"no", "stop", "cancel", "quiet"}:
            self._interrupt_speech()
            self.speak("Okay. Let me know if you need anything else.")
            return True
        if any(word in command for word in ("exit", "quit", "goodbye")):
            self.say_and_log("Goodbye. Shutting down.")
            return False

        if any(phrase in command for phrase in OBJECT_DETECTION_PHRASES):
            if self.throttle.allowed("object_detection"):
                self.speak("Starting object detection.")
                self._start_detection()
            return True

        time_in_match = re.search(r"(?:what(?:'s| is) the time in)\s+(.+)$", command)
        if time_in_match:
            if self.throttle.allowed("time"):
                self.speak(get_world_time(time_in_match.group(1)))
            return True

        if any(phrase in command for phrase in ("what's the time", "what time is it", "what is the time")):
            if self.throttle.allowed("time"):
                self.speak(response_for_phrase("what time is it", self.config))
            return True
        if any(phrase in command for phrase in ("what's the date", "read me the date", "what is the date")):
            if self.throttle.allowed("date"):
                self.speak(response_for_phrase("what's the date", self.config))
            return True
        if "repeat that" in command or "read last message" in command:
            if self.last_spoken_text:
                self.speak(self.last_spoken_text)
            return True

        candidates = (
            "where am i",
            "how to make a fire",
            "how do i filter water",
            "help",
            "list available commands",
            "increase volume",
            "decrease volume",
            "battery level",
            "tell me a joke",
            "what's the weather",
            "read notifications",
            "how do i navigate",
            "call for help",
            "thank you",
            "thanks",
        )
        for phrase in candidates:
            if phrase in command:
                key = {
                    "where am i": "where_am_i",
                    "how to make a fire": "fire",
                    "how do i filter water": "water",
                }.get(phrase, "default")
                if self.throttle.allowed(key):
                    self.speak(response_for_phrase(phrase, self.config))
                return True

        if self.throttle.allowed("default"):
            request_id = int(time.time() * 1_000)
            self.ollama_queue.put((command, request_id))
            try:
                response_id, response = self.ollama_responses.get(
                    timeout=self.config.ollama_timeout + 0.5
                )
                if response_id == request_id:
                    self.speak(response)
                self.ollama_responses.task_done()
            except queue.Empty:
                self.speak("The local language model did not respond in time.")
        return True

    def run(self) -> None:
        for thread in self.threads:
            thread.start()
        if self.config.precache_enabled:
            threading.Thread(target=self._precache, name="tts-precache", daemon=True).start()

        self.say_and_log("Assistant starting up. Please wait.")
        self.say_and_log("Assistant ready. Say help to list commands.")

        with self.sd.RawInputStream(
            samplerate=self.config.sample_rate,
            blocksize=self.config.block_size,
            dtype="int16",
            channels=1,
            callback=self._audio_callback,
        ):
            keep_running = True
            while keep_running and not self.stop_event.is_set():
                raw = self.mic_queue.get()
                try:
                    with self.mode_lock:
                        mode = self.mode
                    if mode == "object_detection":
                        continue

                    if not self.recognizer.AcceptWaveform(raw):
                        continue
                    result = json.loads(self.recognizer.Result())
                    command = result.get("text", "").strip().lower()
                    if not command:
                        continue

                    if mode == "speaking" and command not in {"no", "stop", "cancel", "quiet"}:
                        continue
                    print(f"Heard: {command}")
                    keep_running = self._handle_command(command)
                finally:
                    self.mic_queue.task_done()

    def shutdown(self) -> None:
        if self.stop_event.is_set():
            return
        self.stop_event.set()
        self._interrupt_speech()
        for work_queue in (self.synthesis_queue, self.play_queue, self.ollama_queue):
            try:
                work_queue.put_nowait(None)
            except queue.Full:
                pass
        for thread in self.threads:
            thread.join(timeout=2.0)


def main() -> int:
    config = AssistantConfig.from_env()
    assistant = AccessibleAssistant(config)

    def stop(_signum=None, _frame=None) -> None:
        assistant.shutdown()

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    try:
        assistant.run()
    except KeyboardInterrupt:
        pass
    finally:
        assistant.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
