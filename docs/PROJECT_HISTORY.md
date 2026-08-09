# Project history

This timeline combines the supplied project-development record with verified public competition results. It is not a complete laboratory notebook.

## 2024

- **November:** Initial feasibility experiments used a Raspberry Pi 4 and basic object detection.
- **December:** Development moved to a Raspberry Pi 5 to increase embedded-compute capacity.

## 2025 — engineering and deployment

- **January–February:** YOLOv8 research, project budgeting and hardware procurement.
- **March:** CPU-based object detection achieved only low frame rates, motivating Hailo acceleration. Portable power and accessibility hardware were explored.
- **April:** The training environment moved to WSL Ubuntu 22.04. Early models were trained and exported through ONNX, HAR and HEF. A final YOLOv8m training run was selected for deployment.
- **April–May:** Local speech output, camera-distance work, enclosure design and the offline Vosk assistant were integrated.
- **June–July:** The enclosure was printed and assembled; battery and runtime tests were conducted.
- **August:** VIREO received **Best Innovation** at the North Coast Regional Science Fair.
- **August–September:** Cooling, voice control, camera cabling and the hand-built voice-controlled camera mechanism were refined.
- **October:** VIREO received a **silver medal** at the 45th Eskom Expo International Science Fair in the computing category listing.

## 2026 — international recognition and open-source preparation

- **27–31 January:** VIREO received a **silver medal in computer science** at the IRIS Global Symposium in New Delhi, India.
- **July:** The public repository release was reconstructed from the 2025/2026 reports, recovered scripts, the original HEF model and project imagery. Code was reorganised, hard-coded paths were removed, tests and safety documentation were added, and unsupported claims were separated from reported evidence.

## Provenance note

The repository now uses the project author's confirmed **86,000-image** training-corpus total. Remaining report conflicts concerning exact class composition and benchmark counts are preserved in the model, dataset and performance documentation instead of rewriting the history as if every artefact were available.
