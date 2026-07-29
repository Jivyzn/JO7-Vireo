/*
 * Archived VIREO prototype — Arduino Nano RP2040 ultrasonic belt.
 * Four ultrasonic sensors independently switch four motor-driver outputs.
 */

struct Zone {
  uint8_t triggerPin;
  uint8_t echoPin;
  uint8_t motorPin;
  const char *name;
};

constexpr Zone ZONES[] = {
    {4, 5, 6, "sensor 1"},
    {7, 8, 9, "sensor 2"},
    {10, 11, 12, "sensor 3"},
    {13, 2, 3, "sensor 4"},
};

constexpr float DISTANCE_THRESHOLD_CM = 10.0;
constexpr unsigned long ECHO_TIMEOUT_US = 30000;

float getDistanceCm(uint8_t triggerPin, uint8_t echoPin) {
  digitalWrite(triggerPin, LOW);
  delayMicroseconds(2);
  digitalWrite(triggerPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(triggerPin, LOW);

  const unsigned long duration = pulseIn(echoPin, HIGH, ECHO_TIMEOUT_US);
  if (duration == 0) {
    return -1.0;
  }
  return duration * 0.0343f / 2.0f;
}

void setup() {
  Serial.begin(9600);
  for (const Zone &zone : ZONES) {
    pinMode(zone.triggerPin, OUTPUT);
    pinMode(zone.echoPin, INPUT);
    pinMode(zone.motorPin, OUTPUT);
    digitalWrite(zone.motorPin, LOW);
  }
}

void loop() {
  for (const Zone &zone : ZONES) {
    const float distance = getDistanceCm(zone.triggerPin, zone.echoPin);
    const bool obstacleNear =
        distance > 0 && distance <= DISTANCE_THRESHOLD_CM;
    digitalWrite(zone.motorPin, obstacleNear ? HIGH : LOW);

    Serial.print(zone.name);
    Serial.print(": ");
    if (distance > 0) {
      Serial.print(distance);
      Serial.println(" cm");
    } else {
      Serial.println("timeout");
    }
  }
  delay(100);
}
