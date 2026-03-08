// Motor pins (ESP32)
const int IN1 = 14; // Left Forward
const int IN2 = 26; // Left Backward
const int IN3 = 13; // Right Forward
const int IN4 = 27; // Right Backward (safe boot)

// Buffer for Serial input
String commandBuffer = "";
const String PERIPHERAL_ID = "ESP32_DRIVEBASE";

void setup() {
  Serial.begin(115200);

  // Set motor pins as outputs
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);

  // Ensure motors are off at startup
  stopMotors();
  Serial.println(PERIPHERAL_ID);

}

void loop() {
  // Read Serial input
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') { // Process full line on newline
      commandBuffer.trim();          // remove whitespace
      if (commandBuffer.length() > 0) {
        processCommand(commandBuffer);
      }
      commandBuffer = "";
    } else if (c != '\r') {
      commandBuffer += c;            // accumulate chars
    }
  }
}

// Parse Serial command and control motors
void processCommand(String line) {
  int commaIndex = line.indexOf(',');
  int leftMove = line.substring(0, commaIndex).toInt();
  int rightMove = line.substring(commaIndex + 1).toInt();


  // Left motor control
  if (leftMove > 0) {        // Forward
    digitalWrite(IN1, HIGH);
    digitalWrite(IN2, LOW);
  } else if (leftMove < 0) { // Backward
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, HIGH);
  } else {                   // Stop
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, LOW);
  }

  // Right motor control
  if (rightMove > 0) {       // Forward
    digitalWrite(IN3, HIGH);
    digitalWrite(IN4, LOW);
  } else if (rightMove < 0) { // Backward
    digitalWrite(IN3, LOW);
    digitalWrite(IN4, HIGH);
  } else {                   // Stop
    digitalWrite(IN3, LOW);
    digitalWrite(IN4, LOW);
  }
}

// Stop both motors
void stopMotors() {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);
}
