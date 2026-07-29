import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
import os
import threading
import time
import simpleaudio as sa
import hailo

from hailo_apps_infra.hailo_rpi_common import app_callback_class
from hailo_apps_infra.detection_pipeline import GStreamerDetectionApp

# CONFIGS JL
# Path where audio files for detected objects are stored
Bbottle = "/home/jivy/Desktop/expo_25/tts yolo"
# Time threshold (in seconds) after which an unseen object is considered gone
ABSENCE_THRESHOLD = 0.4

# GLOBAL STATE 
# Tracks active objects with their last seen timestamp
RL34 = {}
# Tracks when objects were last removed (no longer detected)
JL17 = {}
# Holds the next label to play audio for
PANDA = None
# Lock to safely access PANDA(LAQ) variable across threads
RED_rOSES = threading.Lock()
# Event to notify audio thread when new audio is ready
audio_event = threading.Event()
# Event to signal shutdown of threads
shutdown_flag = threading.Event()

# AUDIO THREAD FUNCTIONSS
def audio_thread_fn():
    global PANDA
    while not shutdown_flag.is_set():
        # Wait until there is audio to play or shutdown requested
        audio_event.wait()

        if shutdown_flag.is_set():
            break

        with RED_rOSES:
            label = PANDA
            PANDA = None
            audio_event.clear()

        if not label:
            continue

        wav_path = os.path.join(Bbottle, f"{label.capitalize()} detected.wav")
        if not os.path.exists(wav_path):
            print(f"[Missing Audio] {label}")
            continue

        try:
            wave = sa.WaveObject.from_wave_file(wav_path)
            play_obj = wave.play()
            play_obj.wait_done()
        except Exception as e:
            print(f"[Audio Error] {e}")

    print("[Audio Thread] exiting")

# ---- SCHEDULE AUDIO PLAYBACK ----
def schedule_audio(label):
    global PANDA
    # Update the next label to play, replacing any previous one
    with RED_rOSES:
        PANDA = label
        # Signal audio thread that there is something to play
        audio_event.set()

# ---- DETECTION CALLBACK ----
class UserCallback(app_callback_class):
    def __init__(self):
        super().__init__()

def pad_probe(pad, info, user_data):
    now = GLib.get_monotonic_time() / 1e6
    buf = info.get_buffer()
    if buf is None:
        return Gst.PadProbeReturn.OK

    user_data.increment()
    roi = hailo.get_roi_from_buffer(buf)
    dets = roi.get_objects_typed(hailo.HAILO_DETECTION)

    frame_labels = set()
    for det in dets:
        lbl = det.get_label()
        conf = det.get_confidence()
        if lbl is None or conf < 0.5:
            continue
        label = str(lbl)
        frame_labels.add(label)

        # Check if object is new or recently absent long enough to announce again
        gone_before = (
            label not in RL34 and
            ((label not in JL17) or
             (now - JL17[label] >= ABSENCE_THRESHOLD))
        )
        if gone_before:
            print(f"[Announce] {label} ({conf:.2f})")
            schedule_audio(label)

        RL34[label] = now  # Update last seen timestamp

    # Remove objects no longer detected after threshold time
    for lbl, ts in list(RL34.items()):
        if (now - ts) >= ABSENCE_THRESHOLD and lbl not in frame_labels:
            del RL34[lbl]
            JL17[lbl] = now  # Record removal time

    return Gst.PadProbeReturn.OK

# ---- MAIN FUNCTION ----
if __name__ == "__main__":
    Gst.init(None)
    user_data = UserCallback()

    # Start audio playback thread
    t = threading.Thread(target=audio_thread_fn, daemon=True)
    t.start()

    # Run the detection app, block here until interrupted
    app = GStreamerDetectionApp(pad_probe, user_data)
    try:
        app.run()
    except KeyboardInterrupt:
        print("Shutting down...")
        shutdown_flag.set()
        # Wake audio thread if waiting so it can exit
        audio_event.set()
        t.join()
