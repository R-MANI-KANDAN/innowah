#include <WiFi.h>
#include <HTTPClient.h>
#include <math.h>

#define EEG_PIN 0

float samples[256];

const char* ssid="YOUR_WIFI";
const char* password="YOUR_PASSWORD";
const char* serverURL="https://neuroband-predict-alzheimers.onrender.com/api/hardware_data";

unsigned long lastUpload=0;

float computeRMS(float* data){
  float sum=0;
  for(int i=0;i<256;i++)
    sum+=data[i]*data[i];
  return sqrt(sum/256.0);
}

void setup(){
  Serial.begin(115200);
  WiFi.begin(ssid,password);
  while(WiFi.status()!=WL_CONNECTED) delay(500);
  Serial.println("Headband Connected");
}

void loop(){

  for(int i=0;i<256;i++){
    samples[i]=analogRead(EEG_PIN);
    delayMicroseconds(3900);
  }

  float rms=computeRMS(samples);

  float alpha=rms*0.6;
  float theta=rms*0.45;
  float delta=rms*0.35;
  float beta=rms*0.5;
  float gamma=rms*0.25;

  float theta_alpha_ratio=theta/(alpha+0.01);
  float dominant_frequency=8+(rms/150.0);

  // Serial Plotter
  Serial.print(alpha); Serial.print(",");
  Serial.print(theta); Serial.print(",");
  Serial.print(delta); Serial.print(",");
  Serial.print(beta); Serial.print(",");
  Serial.println(gamma);

  if(millis()-lastUpload>10000){

    lastUpload=millis();

    HTTPClient http;
    http.begin(serverURL);
    http.addHeader("Content-Type","application/json");

    String json="{";
    json+="\"device_id\":\"ESP32_INNOWAH_001\",";
    json+="\"timestamp\":"+String(millis())+",";

    json+="\"eeg\":{";
    json+="\"alpha_power\":"+String(alpha,2)+",";
    json+="\"theta_power\":"+String(theta,2)+",";
    json+="\"delta_power\":"+String(delta,2)+",";
    json+="\"theta_alpha_ratio\":"+String(theta_alpha_ratio,2)+",";
    json+="\"dominant_frequency\":"+String(dominant_frequency,2);
    json+="}";

    json+="}";

    Serial.println(json);
    http.POST(json);
    http.end();
  }

  delay(1000);
}