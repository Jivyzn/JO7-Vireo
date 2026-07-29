# Roadmap

## v1.0 — Public research release

- [x] Recover and clean core Python scripts
- [x] Publish ESP32 ToF belt firmware
- [x] Preserve RP2040 ultrasonic prototype
- [x] Include deployable HEF model and checksum
- [x] Replace hard-coded user paths
- [x] Add optional non-recorded TTS fallback
- [x] Add tests, CI, model card, safety documentation and public recognition record

## v1.1 — Reproducibility

- [ ] Record exact Raspberry Pi OS, kernel, HailoRT and `hailo_apps_infra` versions
- [ ] Recover or rebuild the ONNX/HAR conversion pipeline
- [ ] Publish model input shape and complete class map
- [ ] Add immutable evaluation manifests and standard mAP reporting
- [ ] Add integration tests with recorded Hailo metadata
- [ ] Add a supported systemd service after audio-session testing

## v1.2 — Robust perception

- [ ] Add explicit hazard priority instead of latest-label-only announcements
- [ ] Fuse near-field ToF measurements with visual detections
- [ ] Add low-light/IR evaluation
- [ ] Measure end-to-end latency with synchronised timestamps
- [ ] Add per-class cooldowns and configurable scene summaries
- [ ] Add battery, temperature and health telemetry

## v2.0 — Human-centred validation

- [ ] Ethics-reviewed testing with blind and visually impaired participants
- [ ] Accessible onboarding and emergency-stop design
- [ ] Multilingual offline commands and TTS for South African languages
- [ ] Professionally designed certified power system
- [ ] Lighter enclosure and improved cable management
- [ ] Long-duration reliability, weather and drop testing
- [ ] Regulatory and product-safety review before wider deployment

Roadmap items are proposals, not promises or verified capabilities.
