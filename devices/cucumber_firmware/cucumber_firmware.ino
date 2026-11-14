/*
 * ==============================================================================
 * Project: AIoT Industrial Cold Chain & Sensitive Facility Monitor
 * File: cucumber_firmware.ino
 * Target Board: Cucumber (ESP32)
 * Course: CN466 Project - Internet of Things & AI
 * Author: Chanapa Sadudee (6610680214)
 * ==============================================================================
 * Description:
 *  เฟิร์มแวร์สำหรับบอร์ด Cucumber (ESP32) ทำหน้าที่อ่านค่าอุณหภูมิและความชื้น
 *  จากเซ็นเซอร์ (HTS221 หรือเซ็นเซอร์จำลองบนบอร์ด) เพื่อเฝ้าระวังตู้แช่ยา/ห้อง Server
 *  แล้วส่งข้อมูลในรูปแบบ JSON ผ่านโพรโทคอล MQTT ไปยัง Public Broker (broker.emqx.io)
 * ==============================================================================
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// 1. ตั้งค่าเครือข่าย Wi-Fi
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// 2. ตั้งค่า MQTT Broker
const char* mqtt_server = "broker.emqx.io";
const int mqtt_port = 1883;
const char* mqtt_topic = "tse/cn466/chanapa/telemetry";
const char* client_id = "Cucumber-ColdChain-6610680214";

// 3. กำหนดตัวแปรระบบ
WiFiClient espClient;
PubSubClient client(espClient);
unsigned long lastMsg = 0;
const long interval = 2000; // ส่งข้อมูลทุก 2 วินาที

// กำหนดค่าเริ่มต้นอุณหภูมิห้องแช่เย็น (ช่วงมาตรฐาน 2.0°C - 8.0°C)
float currentTemp = 4.5;
float currentHumid = 60.0;

void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("[WiFi] กำลังเชื่อมต่อกับ: ");
  Serial.println(ssid);

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[WiFi] เชื่อมต่อสำเร็จ!");
    Serial.print("[WiFi] IP Address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n[WiFi] ไม่สามารถเชื่อมต่อได้ (จะลองใหม่ใน loop)");
  }
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("[MQTT] กำลังเชื่อมต่อ Broker...");
    if (client.connect(client_id)) {
      Serial.println(" สำเร็จ!");
      Serial.print("[MQTT] เผยแพร่ที่ Topic: ");
      Serial.println(mqtt_topic);
    } else {
      Serial.print(" ล้มเหลว, rc=");
      Serial.print(client.state());
      Serial.println(" รอ 3 วินาทีแล้วลองใหม่");
      delay(3000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n==========================================");
  Serial.println("  AIoT Cold Chain Monitor - Cucumber v1.0 ");
  Serial.println("==========================================");

  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    setup_wifi();
  }

  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  unsigned long now = millis();
  if (now - lastMsg > interval) {
    lastMsg = now;

    // จำลองการอ่านค่าเซ็นเซอร์ (เดินสุ่มเล็กน้อยตามสภาพแวดล้อมจริง)
    currentTemp += ((float)random(-15, 16)) / 100.0;
    // ควบคุมให้อยู่ในย่านปลอดภัย 3.5°C - 5.5°C
    if (currentTemp < 3.2) currentTemp = 3.5;
    if (currentTemp > 6.5) currentTemp = 6.0;

    currentHumid += ((float)random(-20, 21)) / 100.0;
    if (currentHumid < 50.0) currentHumid = 55.0;
    if (currentHumid > 75.0) currentHumid = 70.0;

    // ประกอบข้อความ JSON
    StaticJsonDocument<256> doc;
    doc["node_id"] = "cucumber-01";
    doc["temp"] = round(currentTemp * 100.0) / 100.0;
    doc["humid"] = round(currentHumid * 100.0) / 100.0;
    doc["uptime_sec"] = millis() / 1000;
    doc["status"] = (currentTemp >= 2.0 && currentTemp <= 8.0) ? "NORMAL" : "ALERT";

    char buffer[256];
    serializeJson(doc, buffer);

    Serial.print("[Sensor Telemetry] ");
    Serial.println(buffer);

    client.publish(mqtt_topic, buffer);
  }
}
