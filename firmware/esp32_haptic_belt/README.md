# ESP32 haptic belt firmware

This is the repository-ready version of the final ESP32/VL53L0X belt firmware contained in the VIREO research report.

## Default wiring

| Function | ESP32 pin |
|---|---:|
| I²C SDA | 21 |
| I²C SCL | 22 |
| Left sensor XSHUT | 14 |
| Centre sensor XSHUT | 27 |
| Right sensor XSHUT | 26 |
| Left motor driver | 18 |
| Centre motor driver | 19 |
| Right motor driver | 23 |

The sensors are reassigned to I²C addresses `0x30`, `0x31`, and `0x32`. The default activation threshold is **300 mm** and can be changed through `DISTANCE_THRESHOLD_MM`.

## Electrical warning

A vibration motor must be powered through a correctly rated transistor or MOSFET stage with appropriate protection and a shared ground. **Never connect a vibration motor directly to an ESP32 GPIO.** Verify the motor supply, current limit, polarity, and battery protection before wearing or testing the belt.

## Arduino dependencies

Install the **Adafruit VL53L0X** library through Arduino Library Manager. Select the correct ESP32 board and serial port before uploading.
