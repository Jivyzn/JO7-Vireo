# Troubleshooting

## `hailo_apps_infra` cannot be imported

Confirm that `HAILO_EXAMPLES_DIR` points to a working Hailo Raspberry Pi examples checkout and that its `setup_env.sh` succeeds manually:

```bash
cd ~/hailo-rpi5-examples
source setup_env.sh
python3 -c 'import hailo_apps_infra; print("OK")'
```

## HEF is incompatible

A HEF may be tied to a particular Hailo architecture and compiler/runtime generation. Record:

```bash
hailortcli --version
hailortcli scan
```

If Hailo reports a model or architecture mismatch, the original ONNX/HAR and matching Dataflow Compiler environment are required to rebuild it.

## Object detection does not stop

Use `scripts/run_object_detection.sh`. The original launcher placed `sleep 15` after the blocking Python process, so it did not impose a 15-second limit. The repository launcher uses GNU `timeout` and sends SIGINT to the application.

## Missing WAV announcements

Personal recordings are optional. Expected names follow this pattern:

```text
Person detected.wav
Chair detected.wav
Bottle detected.wav
```

When a file is missing, VIREO attempts eSpeak. Confirm:

```bash
which espeak-ng
VIREO_ESPEAK_FALLBACK=true
```

## Microphone overflow or dropped words

- confirm the input device and sample rate;
- reduce background noise;
- check that the microphone supports mono 16 kHz capture;
- increase `VIREO_BLOCK_SIZE` if CPU scheduling is unstable;
- avoid running a large Ollama model on the same four-core Pi during voice capture.

## Coqui TTS is slow or unavailable

Set:

```bash
VIREO_TTS_ENGINE=espeak
```

Coqui is optional. If used, allow its model to download and cache before disconnecting the Pi from the internet.

## Servo moves in the wrong direction

The physical camera mount determines whether increasing angle means left or right. Change the sign mapping in `parse_servo_command` or reverse the mount. Do not remove the `0–180°` clamp.

## Servo jitters

- use a stable power supply;
- share ground with the Pi;
- keep the signal cable short;
- reduce mechanical load;
- test without the camera assembly;
- consider hardware PWM for a production revision.

## VL53L0X sensors conflict on I²C

All VL53L0X devices boot at the same default address. Confirm every XSHUT line is independently wired and that the firmware holds all sensors low before enabling and re-addressing them one at a time.

## Undervoltage or random Pi resets

The report encountered insufficient current from early buck converters. Use a supply rated for the Pi, accelerator, camera, audio and peripheral peak load. Check voltage under load, not only at idle.
