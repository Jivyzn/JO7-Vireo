# Release validation record

Validation performed while preparing v1.0.0:

| Check | Result |
|---|---|
| Python bytecode compilation for maintained `src/` and tests | Passed |
| Unit tests for detection state, command parsing and helper functions | **8 passed** |
| Bash syntax for every maintained launcher/installer script | Passed |
| HEF file present and hashed | Passed |
| HEF SHA-256 | `53a92d7db2e43bad67e4426a848767e91981c166f90f9e775caeb5898433a852` |
| Hard-coded `/home/jivy` paths in maintained runtime code | None |
| Credential-pattern review in text source | No credentials found |
| Public award claims | Cross-checked against Eskom Expo, DBE and ITWeb sources |

## Not validated in this build environment

- HailoRT loading of the HEF;
- model compatibility with a particular Hailo accelerator/runtime version;
- CSI camera capture;
- GStreamer pipeline execution;
- microphone and speaker selection;
- Coqui model loading;
- Ollama performance on Raspberry Pi;
- GPIO pulse timing and physical servo direction;
- ESP32 compilation and I²C wiring;
- motor-driver electronics;
- battery safety, runtime or thermal results;
- the reported detection, latency, FPS and accuracy measurements.

These require the original Raspberry Pi/Hailo hardware and an instrumented test environment.
