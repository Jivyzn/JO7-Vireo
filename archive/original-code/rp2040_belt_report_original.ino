#define sybau 4     // trigger pin for ultrasonic sensor 1
#define JL17 5      // echo pin for ultrasonic sensor 1
#define JL34 6      // motor for ultrasonic sensor 1

#define PANDA 7     // trigger pin for ultrasonic sensor 2
#define YO 8        // echo pin for ultrasonic sensor 2
#define GURT 9      // motor for ultrasonic sensor 2

#define VIREO 10    // trigger pin for ultrasonic sensor 3
#define SYFM 11     // echo pin for ultrasonic sensor 3
#define VOX 12      //motor for  ultrasonic sensor 3

#define HTOP 13     // trigger pin for ultrasonic sensor 4
#define AURA 2      // echo pin for ultrasonic sensor 4
#define ZENX 3      // motor for ultrasonic sensor 4

#define DIST_THRESHOLD 10  // distance threshold in cm for leds to react

void setup() {
  Serial.begin(9600);   // using 9600 baud keeps rp2040 stable

  pinMode(sybau, OUTPUT);
  pinMode(JL17, INPUT);
  pinMode(JL34, OUTPUT);
  digitalWrite(JL34, LOW);   // start with motors off

  pinMode(PANDA, OUTPUT);
  pinMode(YO, INPUT);
  pinMode(GURT, OUTPUT);
  digitalWrite(GURT, LOW);   // also off at boot

  pinMode(VIREO, OUTPUT);
  pinMode(SYFM, INPUT);
  pinMode(VOX, OUTPUT);
  digitalWrite(VOX, LOW);

  pinMode(HTOP, OUTPUT);
  pinMode(AURA, INPUT);
  pinMode(ZENX, OUTPUT);
  digitalWrite(ZENX, LOW);   // all motors should start off
}

float getDistanceCM(int trigPin, int echoPin) {
  // short trigger pulse is required
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  // THIS measures echo, 30ms timeout avoids lockups and outages
  long duration = pulseIn(echoPin, HIGH, 30000);

  // convert time to distance in cm
  float distance = duration * 0.0343 / 2.0;
  return distance;
}

void loop() {
  float d1 = getDistanceCM(sybau, JL17);
  Serial.print("Sensor 1 Distance: ");  
  Serial.print(d1);  
  Serial.println(" cm");  
  digitalWrite(JL34, (d1 > 0 && d1 <= DIST_THRESHOLD)? HIGH : LOW);

  float d2 = getDistanceCM(PANDA, YO);
  Serial.print("Sensor 2 Distance: ");  
  Serial.print(d2);  
  Serial.println(" cm");
  digitalWrite(GURT, (d2 > 0 && d2 <= DIST_THRESHOLD)? HIGH : LOW);

  float d3 = getDistanceCM(VIREO, SYFM);
  Serial.print("Sensor 3 Distance: ");  
  Serial.print(d3);  
  Serial.println(" cm");
  digitalWrite(VOX, (d3 > 0 && d3 <= DIST_THRESHOLD)? HIGH : LOW);

  float d4 = getDistanceCM(HTOP, AURA);
  Serial.print("Sensor 4 Distance: ");  
  Serial.print(d4);  
  Serial.println(" cm");
  digitalWrite(ZENX, (d4 > 0 && d4 <= DIST_THRESHOLD) ? HIGH : LOW);

  delay(100);   // small delay keeps things readable n smooth
}
