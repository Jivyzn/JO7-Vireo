/*
 * JØ7 VIREO — ESP32 directional haptic belt
 *
 * Three VL53L0X time-of-flight sensors are assigned unique I2C addresses
 * through their XSHUT pins. Each sensor activates the vibration motor in the
 * corresponding left, centre, or right belt zone when an obstacle is within
 * the configurable threshold.
 *
 * IMPORTANT: Drive each vibration motor through a suitable transistor/MOSFET
 * and flyback protection. Do not power a motor directly from an ESP32 GPIO.
 */

#include <Wire.h>
#include <Adafruit_VL53L0X.h>

namespace Pins {
constexpr uint8_t LEFT_XSHUT = 14;
constexpr uint8_t CENTRE_XSHUT = 27;
constexpr uint8_t RIGHT_XSHUT = 26;

constexpr uint8_t LEFT_MOTOR = 18;
constexpr uint8_t CENTRE_MOTOR = 19;
constexpr uint8_t RIGHT_MOTOR = 23;
}  // namespace Pins

namespace SensorAddress {
constexpr uint8_t LEFT = 0x30;
constexpr uint8_t CENTRE = 0x31;
constexpr uint8_t RIGHT = 0x32;
}  // namespace SensorAddress

constexpr uint16_t DISTANCE_THRESHOLD_MM = 300;
constexpr uint32_t SERIAL_BAUD = 115200;

Adafruit_VL53L0X leftSensor;
Adafruit_VL53L0X centreSensor;
Adafruit_VL53L0X rightSensor;

bool initialiseSensor(Adafruit_VL53L0X &sensor, uint8_t xshutPin,
                      uint8_t address, const char *name) {
  digitalWrite(xshutPin, HIGH);
  delay(10);
  if (!sensor.begin(address)) {
    Serial.print("Failed to initialise ");
    Serial.print(name);
    Serial.println(" VL53L0X sensor.");
    return false;
  }
  return true;
}

void updateZone(Adafruit_VL53L0X &sensor, uint8_t motorPin,
                const char *zoneName) {
  VL53L0X_RangingMeasurementData_t measurement;
  sensor.rangingTest(&measurement, false);

  const bool valid = measurement.RangeStatus == 0;
  const bool obstacleNear =
      valid && measurement.RangeMilliMeter <= DISTANCE_THRESHOLD_MM;

  digitalWrite(motorPin, obstacleNear ? HIGH : LOW);

  Serial.print(zoneName);
  Serial.print(": ");
  if (valid) {
    Serial.print(measurement.RangeMilliMeter);
    Serial.println(" mm");
  } else {
    Serial.print("invalid reading, status=");
    Serial.println(measurement.RangeStatus);
  }
}

void setup() {
  Serial.begin(SERIAL_BAUD);
  Wire.begin(21, 22);

  pinMode(Pins::LEFT_XSHUT, OUTPUT);
  pinMode(Pins::CENTRE_XSHUT, OUTPUT);
  pinMode(Pins::RIGHT_XSHUT, OUTPUT);

  pinMode(Pins::LEFT_MOTOR, OUTPUT);
  pinMode(Pins::CENTRE_MOTOR, OUTPUT);
  pinMode(Pins::RIGHT_MOTOR, OUTPUT);

  digitalWrite(Pins::LEFT_MOTOR, LOW);
  digitalWrite(Pins::CENTRE_MOTOR, LOW);
  digitalWrite(Pins::RIGHT_MOTOR, LOW);

  // Hold every sensor in shutdown to prevent the default-address collision.
  digitalWrite(Pins::LEFT_XSHUT, LOW);
  digitalWrite(Pins::CENTRE_XSHUT, LOW);
  digitalWrite(Pins::RIGHT_XSHUT, LOW);
  delay(10);

  const bool leftReady = initialiseSensor(
      leftSensor, Pins::LEFT_XSHUT, SensorAddress::LEFT, "left");
  const bool centreReady = initialiseSensor(
      centreSensor, Pins::CENTRE_XSHUT, SensorAddress::CENTRE, "centre");
  const bool rightReady = initialiseSensor(
      rightSensor, Pins::RIGHT_XSHUT, SensorAddress::RIGHT, "right");

  if (!(leftReady && centreReady && rightReady)) {
    Serial.println("Sensor initialisation failed. Motors remain disabled.");
    while (true) {
      digitalWrite(Pins::LEFT_MOTOR, LOW);
      digitalWrite(Pins::CENTRE_MOTOR, LOW);
      digitalWrite(Pins::RIGHT_MOTOR, LOW);
      delay(1000);
    }
  }

  Serial.println("VIREO haptic belt ready.");
}

void loop() {
  updateZone(leftSensor, Pins::LEFT_MOTOR, "left");
  updateZone(centreSensor, Pins::CENTRE_MOTOR, "centre");
  updateZone(rightSensor, Pins::RIGHT_MOTOR, "right");
  delay(20);
}
