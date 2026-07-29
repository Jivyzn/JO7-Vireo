"""Voice-controlled SG90 camera-servo controller for Raspberry Pi 5.

This is a cleaned, configurable version of the prototype script supplied by
Jivesh Ramnath.  It keeps the original command vocabulary and common Vosk
misrecognition corrections while moving hardware imports into ``main`` so the
parsing logic can be tested on non-Pi systems.
"""

from __future__ import annotations

import json
import math
import queue
import re
import signal
import threading
import time
from dataclasses import dataclass
from typing import Literal

from .config import ServoConfig

NUM_WORDS = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
}

DIRECTION_CORRECTIONS = {
    "right": "right",
    "rite": "right",
    "write": "right",
    "riot": "right",
    "riots": "right",
    "left": "left",
    "lift": "left",
    "loft": "left",
    "laugh": "left",
    "laughed": "left",
    "laps": "left",
    "leff": "left",
    "laff": "left",
}

_DIRECTION_RE = re.compile(
    r"\b(left|right|rite|write|riot|riots|lift|loft|laugh|laughed|laps|leff|laff)\b"
)


@dataclass(frozen=True)
class ServoCommand:
    kind: Literal["absolute", "relative", "centre", "exit"]
    value: float = 0.0


def parse_number(text: str) -> int | None:
    """Extract a numeric angle from digits or the prototype's word vocabulary."""

    digit_match = re.search(r"\d+", text)
    if digit_match:
        return int(digit_match.group())

    words = text.lower().split()
    for word in words:
        if word in NUM_WORDS:
            return NUM_WORDS[word]
    return None


def parse_servo_command(text: str) -> ServoCommand | None:
    """Convert recognised speech into a servo command."""

    command = text.lower().strip()
    if not command:
        return None
    if any(token in command for token in ("exit", "quit", "stop")):
        return ServoCommand("exit")
    if "center" in command or "centre" in command:
        return ServoCommand("centre")

    direction_match = _DIRECTION_RE.search(command)
    if direction_match:
        degrees = parse_number(command)
        direction = DIRECTION_CORRECTIONS[direction_match.group(0)]
        if degrees is None:
            return None
        signed_delta = float(degrees if direction == "left" else -degrees)
        return ServoCommand("relative", signed_delta)

    degrees = parse_number(command)
    if degrees is not None:
        return ServoCommand("absolute", float(degrees))
    return None


class ServoController:
    """Generate software-timed 50 Hz servo pulses through ``lgpio``."""

    def __init__(self, lgpio_module, config: ServoConfig) -> None:
        self._lgpio = lgpio_module
        self.config = config
        self.period = 1.0 / config.frequency_hz
        self.current_angle = 90.0
        self.chip = self._lgpio.gpiochip_open(0)
        self._lgpio.gpio_claim_output(self.chip, config.pin, 0)

    @staticmethod
    def angle_to_pulse(angle: float) -> float:
        return 0.0005 + (angle / 180.0) * 0.002

    def clamp(self, angle: float) -> float:
        return max(self.config.minimum_angle, min(self.config.maximum_angle, angle))

    def smooth_move(self, target_angle: float, duration: float = 1.0) -> None:
        """Move with sinusoidal ease-out interpolation over approximately duration."""

        target_angle = self.clamp(target_angle)
        steps = max(1, round(duration * self.config.frequency_hz))
        start_angle = self.current_angle

        for index in range(1, steps + 1):
            progress = index / steps
            eased = math.sin(progress * math.pi / 2)
            angle = start_angle + (target_angle - start_angle) * eased
            pulse = self.angle_to_pulse(angle)
            self._lgpio.gpio_write(self.chip, self.config.pin, 1)
            time.sleep(pulse)
            self._lgpio.gpio_write(self.chip, self.config.pin, 0)
            time.sleep(max(0.0, self.period - pulse))

        self.current_angle = target_angle
        print(f"Servo at {round(target_angle)} degrees")

    def execute(self, command: ServoCommand) -> None:
        if command.kind == "centre":
            self.smooth_move(self.config.centre_angle)
        elif command.kind == "absolute":
            self.smooth_move(command.value)
        elif command.kind == "relative":
            self.smooth_move(self.current_angle + command.value)

    def close(self) -> None:
        self._lgpio.gpio_write(self.chip, self.config.pin, 0)
        self._lgpio.gpiochip_close(self.chip)


def main() -> int:
    config = ServoConfig.from_env()
    if not config.vosk_model_path.exists():
        raise FileNotFoundError(
            f"Vosk model not found: {config.vosk_model_path}. "
            "Run scripts/download_vosk_model.sh or set VIREO_VOSK_MODEL."
        )

    try:
        import lgpio
        import pyaudio
        from vosk import KaldiRecognizer, Model
    except ImportError as exc:
        raise SystemExit(
            "Missing servo runtime dependency. See docs/INSTALLATION.md. "
            f"Original error: {exc}"
        ) from exc

    controller = ServoController(lgpio, config)
    commands: queue.Queue[ServoCommand | None] = queue.Queue(maxsize=16)
    stop_event = threading.Event()

    def worker() -> None:
        while not stop_event.is_set():
            item = commands.get()
            try:
                if item is None or item.kind == "exit":
                    return
                controller.execute(item)
            finally:
                commands.task_done()

    thread = threading.Thread(target=worker, name="servo-worker", daemon=True)
    thread.start()

    model = Model(str(config.vosk_model_path))
    recognizer = KaldiRecognizer(model, config.sample_rate)
    microphone = pyaudio.PyAudio()
    stream = microphone.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=config.sample_rate,
        input=True,
        frames_per_buffer=8_000,
    )
    stream.start_stream()

    def request_stop(_signum=None, _frame=None) -> None:
        stop_event.set()
        try:
            commands.put_nowait(None)
        except queue.Full:
            pass

    signal.signal(signal.SIGINT, request_stop)
    signal.signal(signal.SIGTERM, request_stop)

    print("Commands: 'X left', 'X right', 'center', an absolute angle, or 'exit'.")

    try:
        while not stop_event.is_set():
            data = stream.read(4_000, exception_on_overflow=False)
            if not recognizer.AcceptWaveform(data):
                continue

            result = json.loads(recognizer.Result())
            spoken = result.get("text", "").lower().strip()
            if not spoken:
                continue
            print(f"Heard: {spoken}")

            command = parse_servo_command(spoken)
            if command is None:
                print("[WARN] Could not parse a valid servo command.")
                continue
            if command.kind == "exit":
                request_stop()
                break
            try:
                commands.put(command, timeout=0.5)
            except queue.Full:
                print("[WARN] Servo command queue is full; command dropped.")
    finally:
        request_stop()
        thread.join(timeout=2.0)
        controller.close()
        stream.stop_stream()
        stream.close()
        microphone.terminate()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
