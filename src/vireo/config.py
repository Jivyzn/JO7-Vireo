"""Environment-driven configuration for JØ7 VIREO.

The original prototype used hard-coded paths under ``/home/jivy``.  This
module keeps the same defaults conceptually while making every deployment
path configurable and repository-relative.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _path_from_env(name: str, default: Path) -> Path:
    raw = os.getenv(name)
    path = Path(raw).expanduser() if raw else default
    return path.resolve(strict=False)


def _bool_from_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _float_from_env(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number, received {raw!r}") from exc


def _int_from_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, received {raw!r}") from exc


@dataclass(frozen=True)
class AssistantConfig:
    """Configuration for the offline voice assistant."""

    vosk_model_path: Path
    detection_script: Path
    hef_model_path: Path
    audio_cache_dir: Path
    sample_rate: int
    block_size: int
    speaker: str
    tts_model: str
    tts_engine: str
    precache_enabled: bool
    detection_seconds: int
    ollama_model: str
    ollama_timeout: float
    max_ollama_chars: int
    configured_location: str

    @classmethod
    def from_env(cls) -> "AssistantConfig":
        return cls(
            vosk_model_path=_path_from_env(
                "VIREO_VOSK_MODEL",
                PROJECT_ROOT / "models" / "vosk-model-small-en-us-0.15",
            ),
            detection_script=_path_from_env(
                "VIREO_DETECTION_SCRIPT",
                PROJECT_ROOT / "scripts" / "run_object_detection.sh",
            ),
            hef_model_path=_path_from_env(
                "VIREO_HEF_MODEL",
                PROJECT_ROOT / "models" / "yolov8m.hef",
            ),
            audio_cache_dir=_path_from_env(
                "VIREO_AUDIO_CACHE",
                Path.home() / ".cache" / "vireo" / "audio",
            ),
            sample_rate=_int_from_env("VIREO_SAMPLE_RATE", 16_000),
            block_size=_int_from_env("VIREO_BLOCK_SIZE", 2_000),
            speaker=os.getenv("VIREO_TTS_SPEAKER", "p248"),
            tts_model=os.getenv("VIREO_TTS_MODEL", "tts_models/en/vctk/vits"),
            tts_engine=os.getenv("VIREO_TTS_ENGINE", "auto").strip().lower(),
            precache_enabled=_bool_from_env("VIREO_PRECACHE", True),
            detection_seconds=_int_from_env("VIREO_DETECTION_SECONDS", 15),
            ollama_model=os.getenv("VIREO_OLLAMA_MODEL", "llama3"),
            ollama_timeout=_float_from_env("VIREO_OLLAMA_TIMEOUT", 12.0),
            max_ollama_chars=_int_from_env("VIREO_OLLAMA_MAX_CHARS", 280),
            configured_location=os.getenv("VIREO_LOCATION", "").strip(),
        )


@dataclass(frozen=True)
class DetectionConfig:
    """Configuration for Hailo object detection announcements."""

    audio_directory: Path
    audio_enabled: bool
    espeak_fallback: bool
    confidence_threshold: float
    absence_threshold: float

    @classmethod
    def from_env(cls) -> "DetectionConfig":
        return cls(
            audio_directory=_path_from_env(
                "VIREO_AUDIO_DIR",
                PROJECT_ROOT / "assets" / "detection_audio",
            ),
            audio_enabled=_bool_from_env("VIREO_DETECTION_AUDIO", True),
            espeak_fallback=_bool_from_env("VIREO_ESPEAK_FALLBACK", True),
            confidence_threshold=_float_from_env("VIREO_CONFIDENCE", 0.50),
            absence_threshold=_float_from_env("VIREO_ABSENCE_THRESHOLD", 0.40),
        )


@dataclass(frozen=True)
class ServoConfig:
    """Configuration for the voice-controlled camera servo."""

    pin: int
    minimum_angle: float
    maximum_angle: float
    centre_offset: float
    frequency_hz: float
    vosk_model_path: Path
    sample_rate: int

    @property
    def centre_angle(self) -> float:
        return 90.0 + self.centre_offset

    @classmethod
    def from_env(cls) -> "ServoConfig":
        return cls(
            pin=_int_from_env("VIREO_SERVO_PIN", 17),
            minimum_angle=_float_from_env("VIREO_SERVO_MIN_ANGLE", 0.0),
            maximum_angle=_float_from_env("VIREO_SERVO_MAX_ANGLE", 180.0),
            centre_offset=_float_from_env("VIREO_SERVO_CENTRE_OFFSET", -10.0),
            frequency_hz=_float_from_env("VIREO_SERVO_FREQUENCY", 50.0),
            vosk_model_path=_path_from_env(
                "VIREO_VOSK_MODEL",
                PROJECT_ROOT / "models" / "vosk-model-small-en-us-0.15",
            ),
            sample_rate=_int_from_env("VIREO_SAMPLE_RATE", 16_000),
        )
