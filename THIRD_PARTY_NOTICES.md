# Third-party notices

JØ7 VIREO is an integration project. The repository's original code is released under the **GNU Affero General Public License v3.0 or later**, but its dependencies and model toolchains retain their own licences.

| Component | Role | Upstream licence / terms |
|---|---|---|
| Hailo Raspberry Pi 5 examples / `hailo_apps_infra` | GStreamer pipeline and Hailo callbacks | MIT |
| Ultralytics YOLOv8 | Training/export toolchain used to produce the object detector | AGPL-3.0 or Ultralytics Enterprise Licence |
| Vosk | Offline speech recognition | Apache-2.0 |
| Coqui TTS | Optional offline neural text-to-speech | MPL-2.0 |
| Ollama | Optional local model runner | MIT |
| Meta Llama models | Optional Ollama model used by the prototype | Meta Llama Community Licence; model terms are separate from Ollama |
| OpenCV, GStreamer, NumPy, PyAudio, sounddevice, soundfile, simpleaudio, lgpio | Runtime and hardware integration | See each upstream project |
| COCO dataset | Original model-development dataset source described in the report | Dataset/image terms are separate; the dataset is not redistributed here |

## Hailo-derived code

`src/vireo/camera_feed.py` was adapted from the Hailo Raspberry Pi 5 detection examples and from the VIREO prototype callback. Hailo's repository is MIT licensed. The Hailo SDK, Dataflow Compiler, runtime packages, firmware and model binaries may have additional vendor terms; users must obtain them through official Hailo channels.

## Model file

`models/yolov8m.hef` is a compiled deployment artefact supplied by the project author. It was produced through a PyTorch → ONNX → HAR → HEF pipeline described in the research report. Redistribution and use must comply with all applicable upstream model, dataset and toolchain terms. The repository does not grant rights beyond those the author is entitled to grant.

## Voice models and audio

The Vosk language model and any Coqui/VCTK model assets are downloaded separately and are not embedded in this repository. Optional personal WAV announcements are also excluded from the public package.
