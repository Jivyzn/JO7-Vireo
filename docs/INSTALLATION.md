# Installation

## Supported target

The project was developed on Raspberry Pi 5-class hardware with a Hailo AI accelerator and CSI camera. Historical project documents mention both Ubuntu and Raspberry Pi OS across iterations. This guide therefore assumes a **64-bit Debian-based operating system supported by Hailo's current Raspberry Pi 5 packages**.

Use Hailo's official installation guide for the exact OS and package versions required by your Hailo hardware. The conversion toolchain can be version-sensitive; do not assume a HEF compiled for one runtime version will work on every release.

## 1. Prepare the operating system

Update the system and confirm that the camera works before adding VIREO. Enable the correct camera interface and install any firmware required by your camera module.

```bash
sudo apt update
sudo apt full-upgrade -y
sudo reboot
```

## 2. Install Hailo's Raspberry Pi stack

Install HailoRT, the PCIe driver, firmware and Hailo Raspberry Pi examples using official Hailo instructions. VIREO expects a checkout similar to:

```text
~/hailo-rpi5-examples/
├── setup_env.sh
└── ...
```

Check it with:

```bash
hailortcli --version
hailortcli scan
```

The VIREO launcher sources `setup_env.sh` and then imports `hailo_apps_infra`.

## 3. Clone VIREO

```bash
git clone https://github.com/Jivyzn/J07-VIREO.git
cd J07-VIREO
chmod +x scripts/*.sh
```

## 4. Install system and Python dependencies

```bash
./scripts/install_pi.sh
```

The virtual environment is created with `--system-site-packages` so it can access Hailo, GStreamer, `lgpio` and other OS-provided modules.

The default installation uses eSpeak NG as a lightweight offline TTS fallback. To reproduce the original neural TTS path, install Coqui TTS separately inside the virtual environment:

```bash
.venv/bin/pip install 'TTS>=0.22,<1'
```

Coqui may download its selected voice model during first setup. Cache the model before relying on fully offline operation.

## 5. Download Vosk

```bash
./scripts/download_vosk_model.sh
```

This downloads `vosk-model-small-en-us-0.15`, the lightweight English model used by the prototype.

## 6. Configure paths and thresholds

```bash
cp .env.example .env
nano .env
set -a
source .env
set +a
```

Repository-relative paths work when commands are launched from the repository. For services or boot-time launchers, use absolute paths in `.env`.

Important settings:

| Variable | Purpose | Default |
|---|---|---|
| `VIREO_HEF_MODEL` | Compiled Hailo model | `models/yolov8m.hef` |
| `VIREO_VOSK_MODEL` | Vosk model directory | `models/vosk-model-small-en-us-0.15` |
| `HAILO_EXAMPLES_DIR` | Hailo examples checkout | `~/hailo-rpi5-examples` |
| `VIREO_CONFIDENCE` | Detection confidence threshold | `0.50` |
| `VIREO_ABSENCE_THRESHOLD` | Required absence before re-announcement | `0.40` seconds |
| `VIREO_DETECTION_SECONDS` | Timed detection session | `15` seconds |
| `VIREO_TTS_ENGINE` | `auto`, `coqui` or `espeak` | `auto` |
| `VIREO_LOCATION` | Optional manually configured location | blank |

## 7. Verify the environment

```bash
./scripts/verify_environment.sh
```

This checks files and command availability only. It cannot validate the camera, microphone, GPIO electronics or Hailo model compatibility.

## 8. Test object detection

```bash
./scripts/run_object_detection.sh
```

Personal WAV recordings are optional. If `assets/detection_audio/Person detected.wav` is absent, the system uses eSpeak when enabled.

## 9. Test the assistant

```bash
./scripts/run_assistant.sh
```

If Ollama is installed and the selected model is available locally, unmatched commands are sent to it. Otherwise VIREO remains functional with its fixed offline command set.

## 10. Test the servo

Before connecting power:

- confirm the servo supply voltage and current;
- use a shared ground between the Pi and servo supply;
- avoid powering a loaded servo directly from a weak Pi rail;
- confirm GPIO 17 is correct for your build.

Then run:

```bash
./scripts/run_servo.sh
```

## Optional boot service

A systemd service is not enabled automatically because microphones, desktop audio sessions and Hailo environments vary. A template can be created from the following pattern:

```ini
[Unit]
Description=J07 VIREO Assistant
After=network.target sound.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/J07-VIREO
EnvironmentFile=/home/pi/J07-VIREO/.env
ExecStart=/home/pi/J07-VIREO/scripts/run_assistant.sh
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Test manual launch first. Do not install an unattended service until emergency stop, audio level and hardware thermals have been verified.
