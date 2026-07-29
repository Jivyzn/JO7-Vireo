#!/usr/bin/env python3
import lgpio
import time
import json
import re
import math
import queue
import threading
import pyaudio
from vosk import Model, KaldiRecognizer

# === Servo Setup ===
SUS = 17                # This is the GPIO pin where I connected my servo
MIN_ANGLE = 0           # I want to make sure servo never goes below 0°
MAX_ANGLE = 180         # And not above 180°
FREQ = 50               # Standard servo frequency
PERIOD = 1.0 / FREQ
CENTER_OFFSET = -10
Sigma = 90 + CENTER_OFFSET   # My center position with a small offset I figured works best
tamaron = 90                  # I keep track of where the servo currently is

# I open the GPIO chip and claim my servo pin for output
sony = lgpio.gpiochip_open(0)
lgpio.gpio_claim_output(sony, SUS, 0)

# === Servo Utilities ===
def angle_to_pulse(Garnier):
    """I convert an angle to the pulse width the servo understands."""
    return 0.0005 + (Garnier / 180.0) * 0.002

def smooth_move(Ultra, steps=50, duration=1.0):
    """
    I move the servo smoothly instead of snapping it.
    Ultra = target angle
    steps = number of small steps I break the movement into
    duration = total time I want the move to take
    """
    global tamaron
    Ultra = max(MIN_ANGLE, min(MAX_ANGLE, Ultra))
    step_delay = duration / steps
    # I use a sine curve to make the movement smooth and natural
    angles = [tamaron + (Ultra - tamaron) * math.sin((i / steps) * math.pi / 2) for i in range(1, steps+1)]

    for angle in angles:
        pulse = angle_to_pulse(angle)
        lgpio.gpio_write(sony, SUS, 1)
        time.sleep(pulse)
        lgpio.gpio_write(sony, SUS, 0)
        time.sleep(PERIOD - pulse)
        time.sleep(step_delay)
    tamaron = Ultra
    print(f"➡️ Servo at {round(Ultra)}°")

# === Voice Command Parsing ===
# Numbers I want to recognize in words
NUM_WORDS = {
    "zero":0,"one":1,"two":2,"three":3,"four":4,"five":5,"six":6,
    "seven":7,"eight":8,"nine":9,"ten":10,"eleven":11,"twelve":12,
    "thirteen":13,"fourteen":14,"fifteen":15,"sixteen":16,"seventeen":17,
    "eighteen":18,"nineteen":19,"twenty":20,"thirty":30,"forty":40,
    "fifty":50,"sixty":60,"seventy":70,"eighty":80,"ninety":90
}

# Some directions get misheard a lot, so I map them to what I actually mean
DIRECTION_CORRECTIONS = {
    "right": "right", "rite": "right", "write": "right",
    "left": "left", "lift": "left", "loft": "left",
    "riot": "right", "riots": "right",
    "laugh": "left", "laughed": "left", "laps": "left",
    "leff": "left", "laff": "left"
}

def parse_number(Casio):
    """I try to extract a number from what I heard, either digits or words."""
    match = re.search(r"\d+", Casio)
    if match:
        return int(match.group())
    for w in Casio.split():
        if w in NUM_WORDS:
            return NUM_WORDS[w]
    return None

# === Command Queue for Servo Thread ===
Garnier_queue = queue.Queue()  # I put commands here so the servo thread can handle them one by one

def servo_thread():
    """This thread listens to the queue and moves the servo as commands come in."""
    while True:
        Ultra = Garnier_queue.get()
        if Ultra is None:
            break
        smooth_move(Ultra)

# I start the servo thread as a background process
thread = threading.Thread(target=servo_thread, daemon=True)
thread.start()

# === Vosk Speech Recognition Setup ===
model = Model("vosk-model-small-en-us-0.15")
recognizer = KaldiRecognizer(model, 16000)

mic = pyaudio.PyAudio()
stream = mic.open(format=pyaudio.paInt16, channels=1, rate=16000,
                  input=True, frames_per_buffer=8000)
stream.start_stream()

print(" Commands I can say: 'X left', 'X right', 'center', 'exit'")

try:
    while True:
        data = stream.read(4000, exception_on_overflow=False)
        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())
            command = result.get("text", "").lower().strip()
            if not command:
                continue
            print(f"You said: {command}")

            # Exit command
            if any(x in command for x in ["exit", "quit", "stop"]):
                print(" I am exiting now.")
                Garnier_queue.put(None)
                break

            # Center the servo
            if "center" in command:
                Garnier_queue.put(Sigma)
                continue

            # Left/right relative commands
            match = re.search(r"\b(left|right|riot|riots|laugh|laughed|laps|lift|rite|write|leff|laff|loft)\b", command)
            if match:
                word = match.group(0)
                direction = DIRECTION_CORRECTIONS.get(word)
                degrees = parse_number(command)
                if degrees is None or direction is None:
                    print("[WARN] I could not figure out the number or direction.")
                    continue
                # I invert logic for left/right based on how I hear it
                if direction == "left":
                    new_angle = tamaron + degrees
                else:
                    new_angle = tamaron - degrees
                Garnier_queue.put(new_angle)
                continue

            # Absolute number command
            degrees = parse_number(command)
            if degrees is not None:
                Garnier_queue.put(degrees)

except KeyboardInterrupt:
    print("Stopped by me manually.")
    Garnier_queue.put(None)

finally:
    # Clean up everything so I don’t fry the servo or mic
    lgpio.gpio_write(sony, SUS, 0)
    lgpio.gpiochip_close(sony)
    stream.stop_stream()
    stream.close()
    mic.terminate()
