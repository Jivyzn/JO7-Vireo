"""Hailo/GStreamer object detection with low-noise audio announcements.

The callback is adapted from Hailo's MIT-licensed Raspberry Pi 5 examples and
from Jivesh Ramnath's working VIREO prototype.  Hailo's command-line arguments
(e.g. ``-i rpi --hef models/yolov8m.hef``) are intentionally left to
``GStreamerDetectionApp``.
"""

from __future__ import annotations

import os
import queue
import shutil
import signal
import subprocess
import threading
from pathlib import Path

import gi

gi.require_version("Gst", "1.0")
from gi.repository import GLib, Gst  # noqa: E402

import hailo  # noqa: E402
import simpleaudio as sa  # noqa: E402
from hailo_apps_infra.detection_pipeline import GStreamerDetectionApp  # noqa: E402
from hailo_apps_infra.hailo_rpi_common import app_callback_class  # noqa: E402

from .config import DetectionConfig
from .detection_state import Detection, DetectionState

CONFIG = DetectionConfig.from_env()
STATE = DetectionState(absence_threshold=CONFIG.absence_threshold)
SHUTDOWN = threading.Event()


class LatestAnnouncementQueue:
    """A one-slot queue that retains the newest announcement.

    This mirrors the prototype's deliberate anti-flood behaviour: when several
    objects appear at once, the most recent label replaces any pending label
    rather than creating a long, stale narration backlog.
    """

    def __init__(self) -> None:
        self._queue: queue.Queue[str] = queue.Queue(maxsize=1)

    def put_latest(self, label: str) -> None:
        try:
            self._queue.put_nowait(label)
            return
        except queue.Full:
            pass

        try:
            self._queue.get_nowait()
            self._queue.task_done()
        except queue.Empty:
            pass
        self._queue.put_nowait(label)

    def get(self, timeout: float = 0.25) -> str:
        return self._queue.get(timeout=timeout)

    def done(self) -> None:
        self._queue.task_done()


ANNOUNCEMENTS = LatestAnnouncementQueue()


class DetectionAnnouncer:
    def __init__(self, config: DetectionConfig) -> None:
        self.config = config
        self.espeak_binary = shutil.which("espeak-ng") or shutil.which("espeak")

    def _recording_path(self, label: str) -> Path:
        return self.config.audio_directory / f"{label.capitalize()} detected.wav"

    def announce(self, label: str) -> None:
        if not self.config.audio_enabled:
            return

        recording = self._recording_path(label)
        if recording.exists():
            try:
                wave = sa.WaveObject.from_wave_file(str(recording))
                wave.play().wait_done()
                return
            except Exception as exc:  # hardware/audio backend specific
                print(f"[Audio Error] {exc}")

        if self.config.espeak_fallback and self.espeak_binary:
            subprocess.run(
                [self.espeak_binary, f"{label} detected"],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            print(f"[Missing Audio] {recording}")


def audio_worker() -> None:
    announcer = DetectionAnnouncer(CONFIG)
    while not SHUTDOWN.is_set():
        try:
            label = ANNOUNCEMENTS.get(timeout=0.25)
        except queue.Empty:
            continue
        try:
            announcer.announce(label)
        finally:
            ANNOUNCEMENTS.done()
    print("[Audio Thread] exiting")


class UserCallback(app_callback_class):
    pass


def pad_probe(_pad, info, user_data):
    now = GLib.get_monotonic_time() / 1e6
    buffer = info.get_buffer()
    if buffer is None:
        return Gst.PadProbeReturn.OK

    user_data.increment()
    roi = hailo.get_roi_from_buffer(buffer)
    hailo_detections = roi.get_objects_typed(hailo.HAILO_DETECTION)

    detections: list[Detection] = []
    for hailo_detection in hailo_detections:
        label = hailo_detection.get_label()
        confidence = float(hailo_detection.get_confidence())
        if label is None or confidence < CONFIG.confidence_threshold:
            continue
        detections.append(Detection(str(label), confidence))

    for arrival in STATE.update(detections, now):
        print(f"[Announce] {arrival.label} ({arrival.confidence:.2f})")
        ANNOUNCEMENTS.put_latest(arrival.label)

    return Gst.PadProbeReturn.OK


def main() -> int:
    Gst.init(None)
    user_data = UserCallback()
    audio_thread = threading.Thread(target=audio_worker, name="detection-audio", daemon=True)
    audio_thread.start()

    def request_shutdown(_signum=None, _frame=None) -> None:
        SHUTDOWN.set()

    signal.signal(signal.SIGINT, request_shutdown)
    signal.signal(signal.SIGTERM, request_shutdown)

    app = GStreamerDetectionApp(pad_probe, user_data)
    try:
        app.run()
    except KeyboardInterrupt:
        request_shutdown()
    finally:
        request_shutdown()
        audio_thread.join(timeout=3.0)

    return 0


if __name__ == "__main__":
    # Avoid noisy GLib logs unless explicitly requested.
    os.environ.setdefault("GST_DEBUG", "1")
    raise SystemExit(main())
