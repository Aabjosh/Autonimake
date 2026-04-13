#include <Wire.h>
#include<U8g2lib.h>

U8G2_SH1106_128X64_NONAME_F_HW_I2C u8g2(U8G2_R0, U8X8_PIN_NONE);

String line = "";
String PERIPHERAL_ID = "ESP32_SCREEN";

void clearLine() {
  
  u8g2.clear();

  while (Serial.available()) {
    Serial.read();   // flush remaining serial data
  }

  u8g2.clearBuffer();
  u8g2.sendBuffer();
}


void setup() {
  Serial.begin(115200);
  Serial.println(PERIPHERAL_ID);
  u8g2.begin();
  u8g2.setFont(u8g2_font_ncenB08_tr);
}

void loop() {

  bool updated = false;

  while (Serial.available()) {
    char c = Serial.read();

    if (c != '\n' && c != '\r') {
      line += c;
      updated = true;
    } else if (c == '0'){
      clearLine();
    }
  }

  if (updated) {
    u8g2.clearBuffer();
    u8g2.drawStr(0, 20, line.c_str());
    u8g2.sendBuffer();
  }
}
