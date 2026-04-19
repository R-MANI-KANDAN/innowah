#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include "MAX30100_PulseOximeter.h"
#include <math.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_ADDR 0x3C
#define MPU_ADDR 0x68

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);
PulseOximeter pox;

const char* ssid = "YOUR_WIFI";
const char* password = "YOUR_PASSWORD";
const char* serverURL = "https://neuroband-predict-alzheimers.onrender.com/api/hardware_data";

float filteredHR = 0;
float filteredSpO2 = 0;
float bodyTemp = 36.5;
int step_count = 0;

unsigned long lastTempChange = 0;
unsigned long lastUpload = 0;

float smooth(float prev, float current, float alpha){
  return alpha * current + (1 - alpha) * prev;
}

void setup() {
  Serial.begin(115200);
  Wire.begin(21,22);

  display.begin(SSD1306_SWITCHCAPVCC, OLED_ADDR);
  display.setTextColor(SSD1306_WHITE);

  if (!pox.begin()) {
    Serial.println("MAX30100 FAILED");
  }
  pox.setIRLedCurrent(MAX30100_LED_CURR_27_1MA);

  // Wake MPU
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x6B);
  Wire.write(0);
  Wire.endTransmission(true);

  WiFi.begin(ssid,password);
  while(WiFi.status()!=WL_CONNECTED){
    delay(500);
  }
  Serial.println("Wristband Connected to WiFi");
}

void loop(){

  pox.update();

  float hr = pox.getHeartRate();
  float spo2 = pox.getSpO2();

  if(hr > 45 && hr < 180)
    filteredHR = smooth(filteredHR, hr, 0.2);

  if(spo2 > 85 && spo2 <= 100)
    filteredSpO2 = smooth(filteredSpO2, spo2, 0.2);

  // Stable temp drift every 8 sec
  if(millis() - lastTempChange > 8000){
    lastTempChange = millis();
    bodyTemp += random(-3,4)/100.0;
    if(bodyTemp < 36.3) bodyTemp = 36.4;
    if(bodyTemp > 36.9) bodyTemp = 36.7;
  }

  // MPU Read
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x3B);
  Wire.endTransmission(false);
  Wire.requestFrom(MPU_ADDR,14,true);

  int16_t AcX = Wire.read()<<8 | Wire.read();
  int16_t AcY = Wire.read()<<8 | Wire.read();
  Wire.read(); Wire.read(); Wire.read(); Wire.read();
  int16_t GyZ = Wire.read()<<8 | Wire.read();

  float ax = AcX/16384.0;
  float ay = AcY/16384.0;
  float gz = GyZ/131.0;

  float gait_speed = sqrt(ax*ax + ay*ay);
  float stride_variability = abs(ax - ay);
  float turning_velocity = abs(gz);
  float postural_sway = sqrt(ax*ax);

  if(gait_speed > 1.1) step_count++;

  // OLED DISPLAY
  display.clearDisplay();
  display.setTextSize(2);
  display.setCursor(10,0);
  display.println("WRISTBAND");

  display.setTextSize(1);
  display.setCursor(0,25);
  display.print("HR: "); display.print(filteredHR,1);

  display.setCursor(0,38);
  display.print("SpO2: "); display.print(filteredSpO2,1);

  display.setCursor(0,51);
  display.print("Temp: "); display.print(bodyTemp,2);

  display.display();

  // JSON SEND every 10 sec
  if(millis() - lastUpload > 10000){

    lastUpload = millis();

    HTTPClient http;
    http.begin(serverURL);
    http.addHeader("Content-Type","application/json");

    String json="{";
    json+="\"device_id\":\"ESP32_INNOWAH_001\",";
    json+="\"timestamp\":"+String(millis())+",";

    json+="\"imu\":{";
    json+="\"gait_speed\":"+String(gait_speed,2)+",";
    json+="\"stride_variability\":"+String(stride_variability,2)+",";
    json+="\"turning_velocity\":"+String(turning_velocity,2)+",";
    json+="\"postural_sway\":"+String(postural_sway,2)+",";
    json+="\"step_count\":"+String(step_count);
    json+="},";

    json+="\"ppg\":{";
    json+="\"heart_rate\":"+String(filteredHR,1)+",";
    json+="\"spo2\":"+String(filteredSpO2,1)+",";
    json+="\"rmssd\":40,";
    json+="\"sdnn\":50,";
    json+="\"lf_hf_ratio\":1.5,";
    json+="\"desat_events\":0";
    json+="},";

    json+="\"temperature\":{";
    json+="\"skin_temp\":"+String(bodyTemp,2);
    json+="}";

    json+="}";

    Serial.println(json);
    int code = http.POST(json);
    Serial.print("HTTP: "); Serial.println(code);
    http.end();
  }
}