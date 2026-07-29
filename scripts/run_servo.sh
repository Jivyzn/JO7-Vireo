#!/usr/bin/env bash
set -Eeuo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${VIREO_PYTHON:-$ROOT_DIR/.venv/bin/python3}"
[[ -x "$PYTHON_BIN" ]] || PYTHON_BIN="$(command -v python3)"
export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"
exec "$PYTHON_BIN" -m vireo.servo_voice_control
