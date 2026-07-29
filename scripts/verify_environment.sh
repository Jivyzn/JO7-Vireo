#!/usr/bin/env bash
set -u
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FAILED=0

check_file() {
  if [[ -e "$1" ]]; then
    printf '[OK]   %s\n' "$2"
  else
    printf '[MISS] %s — %s\n' "$2" "$1"
    FAILED=1
  fi
}

check_command() {
  if command -v "$1" >/dev/null 2>&1; then
    printf '[OK]   %s (%s)\n' "$2" "$(command -v "$1")"
  else
    printf '[MISS] %s\n' "$2"
    FAILED=1
  fi
}

check_command python3 "Python 3"
check_command timeout "GNU timeout"
check_command espeak-ng "eSpeak NG fallback"
check_file "${VIREO_HEF_MODEL:-$ROOT_DIR/models/yolov8m.hef}" "HEF model"
check_file "${VIREO_VOSK_MODEL:-$ROOT_DIR/models/vosk-model-small-en-us-0.15}" "Vosk model"
check_file "${HAILO_EXAMPLES_DIR:-$HOME/hailo-rpi5-examples}/setup_env.sh" "Hailo examples environment"

if command -v hailortcli >/dev/null 2>&1; then
  printf '[OK]   HailoRT: '
  hailortcli --version 2>/dev/null || true
else
  printf '[MISS] HailoRT CLI\n'
  FAILED=1
fi

if [[ $FAILED -ne 0 ]]; then
  echo "Environment verification found missing requirements." >&2
  exit 1
fi

echo "VIREO environment checks passed. Hardware operation is not tested by this script."
