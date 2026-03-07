#include <Wire.h>
#include<U8g2lib.h>

U8G2_SH1106_128X64_NONAME_F_HW_I2C u8g2(U8G2_R0, U8X8_PIN_NONE);

String line = "";

void clearLine() {
  line = "";                 // reset stored text
  u8g2.clearBuffer();        // clear display buffer
  u8g2.sendBuffer();         // update screen
}


void setup() {
  Serial.begin(9600);
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
    }
  }

  if (updated) {
    u8g2.clearBuffer();
    u8g2.drawStr(0, 20, line.c_str());
    u8g2.sendBuffer();
  }
}
