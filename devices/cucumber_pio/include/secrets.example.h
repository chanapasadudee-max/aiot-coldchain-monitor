#pragma once

// คัดลอกไฟล์นี้เป็น secrets.h แล้วใส่ข้อมูล Wi-Fi ของคุณ
// (ไฟล์ secrets.h ถูกใส่ไว้ใน .gitignore จะไม่ถูกอัปโหลดขึ้น GitHub)

#define WIFI_SSID "YOUR_WIFI_SSID"
#define WIFI_PASSWORD "YOUR_WIFI_PASSWORD"

#define MQTT_SERVER "broker.emqx.io"
#define MQTT_PORT 1883
#define MQTT_TOPIC_TELEMETRY "tse/cn466/chanapa/telemetry"
#define MQTT_TOPIC_CMD "tse/cn466/chanapa/cmd"
#define DEVICE_NODE_ID "cucumber-ris-01"
