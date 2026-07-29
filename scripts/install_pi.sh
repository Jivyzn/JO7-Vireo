#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ "$(uname -m)" != "aarch64" ]]; then
  echo "Warning: this installer is intended for 64-bit Raspberry Pi systems." >&2
fi

sudo apt-get update
sudo apt-get install -y \
  python3-venv python3-pip python3-dev \
  portaudio19-dev python3-pyaudio libsndfile1-dev \
  espeak-ng unzip curl coreutils \
  python3-gi gir1.2-gstreamer-1.0

python3 -m venv --system-site-packages "$ROOT_DIR/.venv"
"$ROOT_DIR/.venv/bin/python" -m pip install --upgrade pip setuptools wheel
"$ROOT_DIR/.venv/bin/pip" install -e "$ROOT_DIR"
"$ROOT_DIR/.venv/bin/pip" install -r "$ROOT_DIR/requirements.txt"

cat <<EOF

Python environment created at $ROOT_DIR/.venv

Next steps:
  1. Install Hailo's Raspberry Pi 5 stack and clone hailo-rpi5-examples.
  2. Run: $ROOT_DIR/scripts/download_vosk_model.sh
  3. Copy .env.example to .env and export the values you need.
  4. Run: $ROOT_DIR/scripts/verify_environment.sh

EOF
