#include <Wire.h>
#include <Adafruit_VL53L0X.h>

Adafruit_VL53L0X Bunny;
Adafruit_VL53L0X pap;
Adafruit_VL53L0X wors;

#define springbok 14
#define protea 27
#define Rbay 26
#define arboretum 18
#define braai 19
#define BunnyLED 23
#define DIST_THRESHOLD 300

void setup() {
  Serial.begin(115200);
  Wire.begin(21, 22);

  pinMode(springbok, OUTPUT);
  pinMode(protea, OUTPUT);
  pinMode(Rbay, OUTPUT);
  pinMode(arboretum, OUTPUT);
  pinMode(braai, OUTPUT);
  pinMode(BunnyLED, OUTPUT);

  digitalWrite(springbok, LOW);
  digitalWrite(protea, LOW);
  digitalWrite(Rbay, LOW);
  delay(10);

  digitalWrite(springbok, HIGH);
  delay(10);
  if (!Bunny.begin(0x30)) while (1);

  digitalWrite(protea, HIGH);
  delay(10);
  if (!pap.begin(0x31)) while (1);

  digitalWrite(Rbay, HIGH);
  delay(10);
  if (!wors.begin(0x32)) while (1);
}

void loop() {
  VL53L0X_RangingMeasurementData_t BunnyData;
  Bunny.rangingTest(&BunnyData, false);
  digitalWrite(arboretum,
               BunnyData.RangeStatus == 0 && BunnyData.RangeMilliMeter <= DIST_THRESHOLD);

  VL53L0X_RangingMeasurementData_t papData;
  pap.rangingTest(&papData, false);
  digitalWrite(braai,
               papData.RangeStatus == 0 && papData.RangeMilliMeter <= DIST_THRESHOLD);

  VL53L0X_RangingMeasurementData_t worsData;
  wors.rangingTest(&worsData, false);
  digitalWrite(BunnyLED,
               worsData.RangeStatus == 0 && worsData.RangeMilliMeter <= DIST_THRESHOLD);

  delay(2);
}
