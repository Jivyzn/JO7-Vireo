#!/usr/bin/env python3
"""
Accessible Assistant for Blind Users (Pi 5 — Ollama threaded, aggressive)
- Keeps custom responses; falls back to Ollama when needed.
- Object detection disables mic for 15s, then resumes.
- Non-blocking Ollama worker so STT/TTS pipeline stays responsive.
- I tuned block sizes, timeouts, and caching for CPU efficiency.
"""

import os
import hashlib
import queue
import threading
import sounddevice as sd
import vosk
import json
import soundfile as sf
from datetime import datetime
from zoneinfo import ZoneInfo
from TTS.api import TTS
import subprocess
import time
import re
import signal
import sys

# -------- CONFIG (kept as you had them) --------
MODEL_PATH = "/home/jivy/Downloads/vosk-model-small-en-us-0.15"
CAMERA_SCRIPT = "/home/jivy/Desktop/expo_25/camera_feed.py"
HEF_PATH = "/home/jivy/Desktop/expo_25/yolov8m.hef"
AUDIO_CACHE_DIR = "/home/jivy/audio_cache"
SPEAKER = "p248"
SAMPLE_RATE = 16000
BLOCKSIZE = 2000           # smaller -> faster reactions on Pi CPU
PRECACHE_ENABLED = True
OBJECT_DETECTION_SCRIPT = "/home/jivy/run_object_detection.sh"
OLLAMA_MODEL = "llama3"    # change if you run another model locally

# ---------- New variable names requested (used, not just declared) ----------
Tspmo = 0.08           # small sleep/poll tuning value I use in short waits
ssbreak = 0.35         # safety short break when switching audio modes
section = 3            # logical section id used for logging/debug
derivative = False     # a simple toggle for extra debug output if I want it
box = {"max_ollama_len": 280, "ollama_timeout": 12}   # tuning box dict
bunny = {"affinity_cores": [2,3]}  # preferred cores for Ollama worker (best-effort)

# Intent cooldowns (unchanged)
INTENT_COOLDOWNS = {
    "object_detection": 20,
    "fire": 10,
    "water": 10,
    "where_am_i": 4,
    "time": 2,
    "date": 2,
    "default": 2
}

os.makedirs(AUDIO_CACHE_DIR, exist_ok=True)
assert os.path.exists(MODEL_PATH), f"Vosk model not found at {MODEL_PATH}"
assert os.path.exists(CAMERA_SCRIPT), f"Camera script not found at {CAMERA_SCRIPT}"
assert os.path.exists(HEF_PATH), f"HEF file not found at {HEF_PATH}"
assert os.path.exists(OBJECT_DETECTION_SCRIPT), f"Object detection script not found at {OBJECT_DETECTION_SCRIPT}"

# --- Load models (I keep this light and synchronous at startup) ---
print("Loading Vosk model (small, CPU-friendly)...")
vosk_model = vosk.Model(MODEL_PATH)
recognizer = vosk.KaldiRecognizer(vosk_model, SAMPLE_RATE)
print("Vosk loaded.")
print("Loading TTS model (may take seconds)...")
tts = TTS(model_name="tts_models/en/vctk/vits", progress_bar=False, gpu=False)
print("TTS loaded.")

# ---------- Queues + State ----------
mic_queue = queue.Queue(maxsize=64)     # mic chunks, bounded so memory doesn't explode
synth_queue = queue.Queue()
play_queue = queue.Queue()
ollama_request_queue = queue.Queue()    # queue to send prompts to Ollama worker
ollama_response_queue = queue.Queue()   # optional: worker can push responses here

sd_lock = threading.Lock()
playing_event = threading.Event()
last_spoken_text = [""]

last_intent_time = {}
intent_lock = threading.Lock()
listening_mode = ["idle"]  # "idle", "speaking", "object_detection"

# ---------- Utility functions ----------
def intent_allowed(key: str, default_cd: int = 2) -> bool:
    """I throttle repeated intents so the Pi doesn’t get swamped."""
    now = time.time()
    cd = INTENT_COOLDOWNS.get(key, default_cd)
    with intent_lock:
        last = last_intent_time.get(key, 0)
        if now - last >= cd:
            last_intent_time[key] = now
            return True
    return False

def text_to_hash_filename_for_chunk(text: str, idx: int) -> str:
    """I cache TTS per text chunk to avoid repeated synthesis."""
    h = hashlib.sha1((text + f"::{idx}").encode("utf-8")).hexdigest()
    return os.path.join(AUDIO_CACHE_DIR, f"{h}.wav")

_SENTENCE_SPLIT_RE = re.compile(r'(?<=[\.\?\!])\s+')

def split_text_into_chunks(text: str, max_chars: int = 220):
    """I split on sentence boundaries first so TTS sounds natural."""
    sentences = _SENTENCE_SPLIT_RE.split(text.strip())
    chunks = []
    cur = ""
    for s in sentences:
        if not s.strip():
            continue
        if len(cur) + len(s) + 1 <= max_chars:
            cur = (cur + " " + s).strip() if cur else s
        else:
            if cur:
                chunks.append(cur.strip())
            cur = s
    if cur:
        chunks.append(cur.strip())
    if not chunks:
        chunks = [text[i:i+max_chars] for i in range(0, len(text), max_chars)]
    return chunks

# ---------- TTS worker ----------
def synth_thread_fn():
    """Background: produce WAVs on demand (or use cached)."""
    while True:
        item = synth_queue.get()
        if item == "STOP":
            break
        chunk_text, idx = item
        fname = text_to_hash_filename_for_chunk(chunk_text, idx)
        if not os.path.exists(fname):
            tmp = fname + ".tmp"
            try:
                tts.tts_to_file(text=chunk_text, speaker=SPEAKER, file_path=tmp)
                os.replace(tmp, fname)
            except Exception as e:
                print("Synthesis error for chunk:", e)
        play_queue.put(fname)
        synth_queue.task_done()

# ---------- Playback worker ----------
def play_thread_fn():
    """Background: play WAVs. Use blocking play to reduce context switching."""
    while True:
        item = play_queue.get()
        if item == "STOP":
            break
        if not os.path.exists(item):
            play_queue.task_done()
            continue
        try:
            playing_event.set()
            with sd_lock:
                # read as float32 for lower CPU jitter on Pi
                data, fs = sf.read(item, dtype="float32")
                sd.play(data, fs, blocking=True)
        except Exception as e:
            print("Play thread error:", e)
        finally:
            playing_event.clear()
            # after TTS ends, go back to idle
            if listening_mode[0] == "speaking":
                listening_mode[0] = "idle"
            play_queue.task_done()

# ---------- Ollama worker (threaded, non-blocking) ----------
def ollama_worker_fn():
    """
    I run Ollama in a dedicated thread so it doesn't block voice I/O.
    I also attempt to set CPU affinity for Ollama if allowed (best-effort).
    """
    # Best-effort CPU affinity (may require root or platform support)
    try:
        if hasattr(os, "sched_setaffinity") and bunny.get("affinity_cores"):
            os.sched_setaffinity(0, set(bunny["affinity_cores"]))
            if derivative:
                print(f"[OLLAMA] affinity set to {bunny['affinity_cores']}")
    except Exception as e:
        # Not fatal — just continue without affinity
        if derivative:
            print("OLLAMA affinity not set:", e)

    while True:
        item = ollama_request_queue.get()
        if item == "STOP":
            break
        prompt, req_id = item  # req_id optional for tracing
        try:
            # Run ollama with timeout and trim output aggressively
            proc = subprocess.run(
                ["ollama", "run", OLLAMA_MODEL],
                input=prompt.encode("utf-8"),
                capture_output=True,
                text=True,
                check=False,
                timeout=box.get("ollama_timeout", 12)
            )
            out = proc.stdout.strip()
            # take last non-empty line as most relevant; trim to max length
            if out:
                lines = [l for l in out.splitlines() if l.strip()]
                resp = lines[-1] if lines else out
                resp = resp.strip()[: box.get("max_ollama_len", 280)]
            else:
                resp = "Sorry, I received no answer from Ollama."
        except subprocess.TimeoutExpired:
            resp = "Sorry, the language model timed out."
        except Exception as e:
            resp = "Sorry, Ollama failed: " + str(e)
        # push response to main path (synth & speak)
        ollama_response_queue.put((req_id, resp))
        ollama_request_queue.task_done()
        # short breathing room so worker loop isn't hot-spinning
        time.sleep(Tspmo)

# ---------- Pre-cache common responses (optional) ----------
def precache_common_responses():
    """I create cached WAV files for the fixed replies to save CPU later."""
    if not PRECACHE_ENABLED:
        return
    print("Caching common responses...")
    for text in set(custom_responses.values()):
        chunks = split_text_into_chunks(text, max_chars=220)
        for idx, chunk in enumerate(chunks):
            fn = text_to_hash_filename_for_chunk(chunk, idx)
            if os.path.exists(fn):
                continue
            tmp = fn + ".tmp"
            try:
                tts.tts_to_file(text=chunk, speaker=SPEAKER, file_path=tmp)
                os.replace(tmp, fn)
            except Exception as e:
                print("Cache error:", e)
    print("Caching done.")

# ---------- Speak helper ----------
def speak(text: str):
    """Top-level speak: enqueue cached audio or request synthesis."""
    if not text:
        return
    last_spoken_text[0] = text
    listening_mode[0] = "speaking"
    chunks = split_text_into_chunks(text, max_chars=240)
    for idx, chunk in enumerate(chunks):
        fname = text_to_hash_filename_for_chunk(chunk, idx)
        if os.path.exists(fname):
            play_queue.put(fname)
        else:
            synth_queue.put((chunk, idx))

def say_and_log(text: str):
    print(text)
    speak(text)

def error_and_speak(msg: str):
    print("ERROR:", msg)
    speak("Error: " + msg)

# ---------- Custom Responses (kept) ----------
custom_responses = {
    "where am i": "You are at: Emporers Palace, Kempton Park, Johannesburg , South Africa.",
    "how to make a fire": (
        "To start a fire quickly in the wild, first gather dry tinder such as dry grass, dead leaves, or fine bark shavings. "
        "Next collect kindling: thin sticks about the size of a pencil. Also gather a few larger pieces of wood for fuel. "
        "Clear a safe patch of ground and build a small teepee or lean-to with the tinder in the center so air can circulate. "
        "Light the tinder with matches, a lighter, or sparks from a ferro rod. Once you have a small flame, gently blow at its base to supply oxygen. "
        "As flames grow, add kindling, then larger sticks to stabilize the fire. Never leave the fire unattended and always have water or dirt to fully extinguish it."
    ),
    "how do i filter water": (
        "To filter water in the wild, choose a flowing source like a stream if possible. Avoid stagnant pools. "
        "Use a clean cloth to strain out large particles. Boil the water for at least one minute. "
        "If you can't boil, use water purification tablets or a portable filter. "
        "As an emergency measure, you can build a filter using sand, gravel, and charcoal, but always try to boil or use tablets if possible."
    ),
    "what objects are around me": "Starting object detection.",
    "what's in front of me": "Starting object detection.",
    "read me the date": "Today's date is " + datetime.now().strftime("%A, %B %d, %Y") + ".",
    "what's the date": "Today's date is " + datetime.now().strftime("%A, %B %d, %Y") + ".",
    "what time is it": "The local time is " + datetime.now().strftime("%I:%M %p") + ".",
    "what's the time": "The local time is " + datetime.now().strftime("%I:%M %p") + ".",
    "repeat that": "Repeating the last message.",
    "help": (
        "You can ask me questions like: "
        "'How do I make a fire?', 'How do I filter water?', 'What's around me?', "
        "'What's the time?', 'What's the date?', 'Where am I?', or say 'stop' or 'no' to interrupt me."
    ),
    "what's nearby": "Starting object detection.",
    "describe surroundings": "Starting object detection.",
    "increase volume": "Increasing the volume.",
    "decrease volume": "Decreasing the volume.",
    "battery level": "Battery level is currently not available.",
    "tell me a joke": "Why did the scarecrow win an award? Because he was outstanding in his field.",
    "what's the temperature": "Temperature information is not currently available.",
    "what's the weather": "Weather information is not currently available.",
    "read notifications": "You have no new notifications.",
    "read last message": "Repeating the last message.",
    "how do i navigate": (
        "You can navigate by asking what objects are around you or in front of you. "
        "Use your cane and follow tactile ground markers. If you need assistance, ask for help or call a nearby person."
    ),
    "call for help": "To call for help, use your phone or a designated emergency button if available.",
    "list available commands": (
        "You can say: 'where am I', 'how to make a fire', 'how do I filter water', 'what objects are around me', 'what's in front of me', "
        "'what is the date', 'what's the time', 'repeat that', 'help', 'increase volume', 'decrease volume', 'tell me a joke', or 'call for help'."
    ),
    "thank you": "You're most welcome.",
    "thanks": "You're most welcome.",
}

# ---------- Object Detection runner ----------
def run_object_detection_for_15s():
    """Launch object detection in a new terminal, block mic for 15s."""
    def detection_thread():
        listening_mode[0] = "object_detection"
        try:
            subprocess.Popen(["lxterminal", "--command", OBJECT_DETECTION_SCRIPT])
            time.sleep(15)
        except Exception as e:
            print("run_object_detection error:", e)
        finally:
            # small safe break so audio layers can settle
            time.sleep(ssbreak)
            listening_mode[0] = "idle"
    threading.Thread(target=detection_thread, daemon=True).start()

# ---------- Main listening loop ----------
def listen_and_respond():
    """Main loop: feed mic chunks into Vosk and handle intents / Ollama fallback."""
    say_and_log("Assistant starting up. Please wait.")
    time.sleep(0.2)
    say_and_log("Assistant ready. Say 'help' to list commands.")

    # RawInputStream with callback to keep main loop lean
    with sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=BLOCKSIZE,
                           dtype='int16', channels=1,
                           callback=lambda indata, frames, t, s: mic_queue.put(bytes(indata))):
        # Poll loops are compact and reaction-focused for Pi CPU
        while True:
            raw = mic_queue.get()   # blocking get - cheap in CPU cycles

            # If OD is running, ignore input
            if listening_mode[0] == "object_detection":
                continue

            # If speaking, accept only interruptions
            if listening_mode[0] == "speaking":
                if recognizer.AcceptWaveform(raw):
                    res = json.loads(recognizer.Result())
                    command = res.get("text", "").strip().lower()
                    if command in ["no", "stop", "cancel", "quiet"]:
                        sd.stop()
                        playing_event.clear()
                        listening_mode[0] = "idle"
                        speak("Okay, let me know if you need anything else.")
                continue

            # Idle: fully listen and route commands
            if listening_mode[0] == "idle":
                if recognizer.AcceptWaveform(raw):
                    res = json.loads(recognizer.Result())
                    command = res.get("text", "").strip().lower()
                    if not command:
                        continue
                    if derivative:
                        print(f"[SECTION {section}] FINAL heard:", command)

                    # global interrupts
                    if command in ["no", "stop", "cancel", "quiet"]:
                        sd.stop()
                        speak("Okay, let me know if you need anything else.")
                        continue
                    if any(word in command for word in ["exit", "quit", "goodbye"]):
                        if intent_allowed("default"):
                            say_and_log("Goodbye. Shutting down.")
                            time.sleep(0.5)
                        break

                    # object detection triggers
                    if any(kw in command for kw in [
                        "what objects are around me", "what's in front of me", "what objects are near me",
                        "what's nearby", "describe surroundings"
                    ]):
                        if intent_allowed("object_detection"):
                            run_object_detection_for_15s()
                        continue

                    # time / date
                    if "what's the time in" in command or "what is the time in" in command:
                        try:
                            city = command.split("time in", 1)[1].strip()
                            if intent_allowed("time"):
                                speak(get_world_time(city))
                        except Exception:
                            speak("Sorry, I couldn't parse the city. Say 'what's the time in London' for example.")
                        continue
                    if "what's the time" in command or "what time is it" in command or "what time" in command:
                        if intent_allowed("time"):
                            now = datetime.now()
                            speak("The local time is " + now.strftime("%I:%M %p") + ".")
                        continue
                    if "what's the date" in command or "read me the date" in command or "what is the date" in command:
                        if intent_allowed("date"):
                            speak(custom_responses.get("read me the date"))
                        continue

                    # repeat last
                    if "repeat that" in command or "read last message" in command:
                        last = last_spoken_text[0]
                        if last:
                            speak(last)
                        continue

                    # try matching custom responses
                    handled = False
                    for phrase, answer in custom_responses.items():
                        if phrase in command:
                            # decide intent key for cooldowns
                            if phrase in ["how to make a fire"]:
                                key = "fire"
                            elif phrase in ["how do i filter water"]:
                                key = "water"
                            elif phrase in ["where am i"]:
                                key = "where_am_i"
                            elif phrase in [
                                "what objects are around me", "what's in front of me", "what objects are near me",
                                "what's nearby", "describe surroundings"
                            ]:
                                key = "object_detection"
                            else:
                                key = "default"
                            if intent_allowed(key):
                                speak(answer)
                            handled = True
                            break
                    if handled:
                        continue

                    # nothing matched -> send to Ollama worker (non-blocking)
                    if intent_allowed("default"):
                        # push prompt to Ollama queue and wait for its response with timeout
                        req_id = int(time.time()*1000)
                        ollama_request_queue.put((command, req_id))
                        # Wait briefly for worker to push back result; don't block long
                        try:
                            # give the worker a short window to answer before fallback message
                            resp_id, resp_text = ollama_response_queue.get(timeout=box.get("ollama_timeout", 12))
                            # only speak if the response corresponds to our request (req_id not strictly enforced, but helpful)
                            speak(resp_text)
                            ollama_response_queue.task_done()
                        except queue.Empty:
                            # If no result in time, say a polite fallback and continue (worker will still finish and cache)
                            speak("I'm thinking... I'll answer as soon as I can.")
                            # we don't block; worker will put its answer into ollama_response_queue for next read if wanted

# ---------- Helper: world time ----------
city_timezones = {
    "cape town": "Africa/Johannesburg", "johannesburg": "Africa/Johannesburg",
    "lagos": "Africa/Lagos", "nairobi": "Africa/Nairobi", "casablanca": "Africa/Casablanca",
    "tokyo": "Asia/Tokyo", "new york": "America/New_York", "london": "Europe/London",
}

def get_world_time(city: str) -> str:
    tz = city_timezones.get(city.lower())
    if not tz:
        return f"Sorry, I don't have time info for {city}."
    now = datetime.now(ZoneInfo(tz))
    return f"The time in {city.title()} is {now.strftime('%I:%M %p')}."

# ---------- Shutdown ----------
def shutdown(signum=None, frame=None):
    """Clean shutdown: stop threads and exit."""
    say_and_log("Assistant shutting down. Goodbye.")
    # ask threads to stop
    synth_queue.put("STOP")
    play_queue.put("STOP")
    ollama_request_queue.put("STOP")
    # small pause for threads to close gracefully
    time.sleep(0.3)
    os._exit(0)

# ---------- Start workers + main ----------
if __name__ == "__main__":
    # signal handling
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # start TTS & playback workers
    synth_thread = threading.Thread(target=synth_thread_fn, daemon=True)
    synth_thread.start()
    play_thread = threading.Thread(target=play_thread_fn, daemon=True)
    play_thread.start()

    # start Ollama worker separate thread (aggressive but non-blocking)
    ollama_thread = threading.Thread(target=ollama_worker_fn, daemon=True)
    ollama_thread.start()

    # optional pre-cache (one-time cost)
    if PRECACHE_ENABLED:
        cache_thread = threading.Thread(target=precache_common_responses, daemon=True)
        cache_thread.start()

    try:
        listen_and_respond()
    except KeyboardInterrupt:
        shutdown()
    except Exception as e:
        error_and_speak(f"Fatal error: {e}")
        shutdown()
