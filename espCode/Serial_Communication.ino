#include <Wire.h>
#include<U8g2lib.h>

U8G2_SH1106_128X64_NONAME_F_HW_I2C u8g2(U8G2_R0, U8X8_PIN_NONE);

const String PERIPHERAL_ID = "ESP32_SCREEN" // peripheral id number

void setup() {
  Serial.begin(115200);
  u8g2.begin();
  u8g2.setFont(u8g2_font_ncenB08_tr);
  Serial.println(PERIPHERAL_ID);
}

void loop() {
  // put your main code here, to run repeatedly:

  if(Serial.available()){
     String cmd = Serial.readStringUntil('\n'); 

    //  Serial.print("received!");
    //  Serial.println(cmd);

    u8g2.clearBuffer();
    u8g2.drawStr(0,25,cmd.c_str());
    u8g2.sendBuffer();

  }

}
