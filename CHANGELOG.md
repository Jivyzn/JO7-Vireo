# Changelog

All notable changes to the public repository are documented here.

## [1.0.0] — 2026-07-29

### Added

- Clean Python package for the offline assistant, Hailo detection callback and servo controller
- ESP32/VL53L0X haptic-belt firmware
- Archived RP2040 ultrasonic prototype
- Timed Hailo launcher with environment checks
- Included `yolov8m.hef` deployment model and SHA-256 record
- Repository-relative configuration through environment variables
- eSpeak fallback when personal WAV recordings are unavailable
- Hardware-independent unit tests and GitHub Actions CI
- Architecture, installation, model, dataset, performance, safety and troubleshooting documentation
- Research report, project images and verified public recognition links
- AGPL-3.0-or-later licence and third-party notices

### Corrected from prototype

- Removed hard-coded `/home/jivy/...` paths
- Replaced ineffective post-process `sleep 15` with GNU `timeout`
- Corrected Ollama text-mode subprocess input
- Prevented microphone callback blocking through a bounded queue
- Made relative servo commands execute against the latest physical command state
- Removed duplicated and ambiguous prototype variable names from maintained code
