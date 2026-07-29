#!/usr/bin/env bash
set -Eeuo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODEL_NAME="vosk-model-small-en-us-0.15"
DESTINATION="$ROOT_DIR/models/$MODEL_NAME"
ARCHIVE="$(mktemp --suffix=.zip)"
trap 'rm -f "$ARCHIVE"' EXIT

if [[ -d "$DESTINATION" ]]; then
  echo "Vosk model already exists: $DESTINATION"
  exit 0
fi

curl -fL "https://alphacephei.com/vosk/models/$MODEL_NAME.zip" -o "$ARCHIVE"
unzip -q "$ARCHIVE" -d "$ROOT_DIR/models"
echo "Installed Vosk model at: $DESTINATION"
