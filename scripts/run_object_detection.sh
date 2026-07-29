#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HAILO_EXAMPLES_DIR="${HAILO_EXAMPLES_DIR:-$HOME/hailo-rpi5-examples}"
HEF_MODEL="${VIREO_HEF_MODEL:-$ROOT_DIR/models/yolov8m.hef}"
DURATION="${VIREO_DETECTION_SECONDS:-15}"
PYTHON_BIN="${VIREO_PYTHON:-$ROOT_DIR/.venv/bin/python3}"

if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="$(command -v python3)"
fi
if [[ ! -f "$HAILO_EXAMPLES_DIR/setup_env.sh" ]]; then
  echo "Hailo setup_env.sh not found at: $HAILO_EXAMPLES_DIR" >&2
  echo "Set HAILO_EXAMPLES_DIR to your hailo-rpi5-examples checkout." >&2
  exit 1
fi
if [[ ! -f "$HEF_MODEL" ]]; then
  echo "HEF model not found: $HEF_MODEL" >&2
  exit 1
fi
if ! command -v timeout >/dev/null 2>&1; then
  echo "The GNU timeout command is required (package: coreutils)." >&2
  exit 1
fi

# Hailo's setup script exports the runtime and hailo_apps_infra environment.
pushd "$HAILO_EXAMPLES_DIR" >/dev/null
# shellcheck disable=SC1091
source setup_env.sh
popd >/dev/null

export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

# SIGINT lets the GStreamer application and audio worker shut down cleanly.
exec timeout --signal=INT --kill-after=5s "${DURATION}s" \
  "$PYTHON_BIN" -m vireo.camera_feed -i rpi --hef "$HEF_MODEL"
