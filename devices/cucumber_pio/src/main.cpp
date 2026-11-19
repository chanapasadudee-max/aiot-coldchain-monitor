/*
 * ==============================================================================
 * Project: AIoT Industrial Cold Chain & Sensitive Facility Monitor
 * Board:   Gravitech Cucumber RIS (ESP32-S2)
 * Features:
 *   1. I2C Auto-Discovery (SDA=41, SCL=40): HTS221 + BMP280 + MPU6050
 *   2. High-rate Vibration/Shock Peak Sampling (MPU6050)
 *   3. Bidirectional MQTT:
 *      - Publish Telemetry JSON -> tse/cn466/chanapa/telemetry
 *      - Subscribe Commands     <- tse/cn466/chanapa/cmd
 *   4. Physical Actuator: Onboard NeoPixel RGB LED (GPIO 18) + Built-in LED (GPIO 2)
 * ==============================================================================
 */

#include <Arduino.h>
#include <WiFi.h>
#include <Wire.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_HTS221.h>
#include <Adafruit_BMP280.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_NeoPixel.h>

#include "secrets.h"

// Hardware Pins (Cucumber RIS ESP32-S2)
#define I2C_SDA_PIN 41
#define I2C_SCL_PIN 40
#define NEOPIXEL_PIN 18
#define BUILTIN_LED_PIN 2

WiFiClient espClient;
PubSubClient mqtt(espClient);

Adafruit_HTS221 hts;
Adafruit_BMP280 bmp;
Adafruit_MPU6050 mpu;
Adafruit_NeoPixel pixel(1, NEOPIXEL_PIN, NEO_GRB + NEO_KHZ800);

bool hasHTS = false;
bool hasBMP = false;
bool hasMPU = false;

// LED Actuator State
String currentLedMode = "safe";
uint8_t customR = 0, customG = 180, customB = 80;
unsigned long lastBlinkMs = 0;
bool blinkState = false;

// Telemetry & Vibration Sampling
unsigned long lastPubMs = 0;
unsigned long lastSampleMs = 0;
const unsigned long PUB_INTERVAL_MS = 2000;
float peakVibG = 0.0f;
bool shockFlag = false;
const float SHOCK_THRESHOLD_G = 0.35f;

void setPixelColorSafe(uint8_t r, uint8_t g, uint8_t b) {
  pixel.setPixelColor(0, pixel.Color(r, g, b));
  pixel.show();
}

void applyLedMode(const String& mode, uint8_t r = 0, uint8_t g = 0, uint8_t b = 0) {
  currentLedMode = mode;
  if (mode == "safe" || mode == "normal") {
    setPixelColorSafe(0, 140, 55); // Emerald Green
    digitalWrite(BUILTIN_LED_PIN, LOW);
  } else if (mode == "warning" || mode == "warn") {
    setPixelColorSafe(255, 170, 0); // TSE Gold/Amber
    digitalWrite(BUILTIN_LED_PIN, HIGH);
  } else if (mode == "critical" || mode == "crit") {
    setPixelColorSafe(255, 0, 20); // TSE Crimson Red
    digitalWrite(BUILTIN_LED_PIN, HIGH);
  } else if (mode == "off") {
    setPixelColorSafe(0, 0, 0);
    digitalWrite(BUILTIN_LED_PIN, LOW);
  } else if (mode == "custom") {
    customR = r; customG = g; customB = b;
    setPixelColorSafe(r, g, b);
  }
  Serial.print("[ACTUATOR] LED mode set -> ");
  Serial.println(currentLedMode);
}

void updateLedAnimation() {
  if (currentLedMode == "critical" || currentLedMode == "crit") {
    unsigned long now = millis();
    if (now - lastBlinkMs >= 300) {
      lastBlinkMs = now;
      blinkState = !blinkState;
      if (blinkState) {
        setPixelColorSafe(255, 0, 20);
        digitalWrite(BUILTIN_LED_PIN, HIGH);
      } else {
        setPixelColorSafe(30, 0, 0);
        digitalWrite(BUILTIN_LED_PIN, LOW);
      }
    }
  }
}

void scanI2C() {
  Serial.println("[I2C] Scanning bus (SDA=41, SCL=40)...");
  int found = 0;
  for (uint8_t addr = 1; addr < 127; addr++) {
    Wire.beginTransmission(addr);
    if (Wire.endTransmission() == 0) {
      Serial.print("  -> Found I2C device at 0x");
      if (addr < 16) Serial.print("0");
      Serial.println(addr, HEX);
      found++;
    }
  }
  Serial.printf("[I2C] Scan complete. Total devices: %d\n", found);
}

void onMqttMessage(char* topic, byte* payload, unsigned int length) {
  String msg;
  for (unsigned int i = 0; i < length; i++) {
    msg += (char)payload[i];
  }
  Serial.print("[MQTT CMD] ");
  Serial.println(msg);

  JsonDocument doc;
  DeserializationError err = deserializeJson(doc, msg);
  if (err) {
    Serial.println("[MQTT CMD] Invalid JSON ignored.");
    return;
  }

  String cmd = doc["cmd"] | "";
  if (cmd == "set_led") {
    String mode = doc["mode"] | "safe";
    uint8_t r = doc["r"] | 0;
    uint8_t g = doc["g"] | 0;
    uint8_t b = doc["b"] | 0;
    applyLedMode(mode, r, g, b);
  } else if (cmd == "ping") {
    JsonDocument ack;
    ack["node_id"] = DEVICE_NODE_ID;
    ack["ack"] = "pong";
    ack["led_mode"] = currentLedMode;
    ack["uptime_sec"] = millis() / 1000;
    char out[192];
    serializeJson(ack, out);
    mqtt.publish(MQTT_TOPIC_TELEMETRY, out);
  }
}

void setupWiFi() {
  if (WiFi.status() == WL_CONNECTED) return;
  Serial.print("[WiFi] Connecting to ");
  Serial.println(WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int tries = 0;
  while (WiFi.status() != WL_CONNECTED && tries < 30) {
    delay(400);
    Serial.print(".");
    tries++;
  }
  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("\n[WiFi] Connected! IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n[WiFi] Connection timeout, will retry.");
  }
}

void reconnectMqtt() {
  if (WiFi.status() != WL_CONNECTED) return;
  if (mqtt.connected()) return;

  String clientId = String("Cucumber-RIS-") + String(random(0xffff), HEX);
  Serial.print("[MQTT] Connecting as ");
  Serial.print(clientId);
  if (mqtt.connect(clientId.c_str())) {
    Serial.println(" -> OK!");
    mqtt.subscribe(MQTT_TOPIC_CMD);
    Serial.print("[MQTT] Subscribed CMD: ");
    Serial.println(MQTT_TOPIC_CMD);
  } else {
    Serial.printf(" -> failed rc=%d\n", mqtt.state());
  }
}

void sampleVibration() {
  if (!hasMPU) return;
  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);
  // Compute acceleration magnitude in g (1g = 9.80665 m/s^2) and subtract gravity
  float magG = sqrt(a.acceleration.x * a.acceleration.x +
                    a.acceleration.y * a.acceleration.y +
                    a.acceleration.z * a.acceleration.z) / 9.80665f;
  float deltaG = fabs(magG - 1.0f);
  if (deltaG > peakVibG) {
    peakVibG = deltaG;
  }
  if (deltaG >= SHOCK_THRESHOLD_G) {
    shockFlag = true;
  }
}

void setup() {
  Serial.begin(115200);
  delay(800);
  Serial.println("\n====================================================");
  Serial.println("  AIoT Cold Chain Monitor — Cucumber RIS (ESP32-S2) ");
  Serial.println("====================================================");

  pinMode(BUILTIN_LED_PIN, OUTPUT);
  pixel.begin();
  pixel.setBrightness(55);
  setPixelColorSafe(0, 80, 200); // Booting Blue

  Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);
  scanI2C();

  if (hts.begin_I2C()) {
    hasHTS = true;
    Serial.println("[SENSOR] HTS221 ready (Temp/Humid)");
  }
  if (bmp.begin(0x76) || bmp.begin(0x77)) {
    hasBMP = true;
    Serial.println("[SENSOR] BMP280 ready (Pressure)");
  }
  if (mpu.begin(0x68) || mpu.begin(0x69)) {
    hasMPU = true;
    mpu.setAccelerometerRange(MPU6050_RANGE_4_G);
    mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
    Serial.println("[SENSOR] MPU6050 ready (Vibration/Shock)");
  }

  setupWiFi();
  mqtt.setServer(MQTT_SERVER, MQTT_PORT);
  mqtt.setCallback(onMqttMessage);
  mqtt.setBufferSize(512);
  reconnectMqtt();

  applyLedMode("safe");
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    setupWiFi();
  }
  if (!mqtt.connected()) {
    static unsigned long lastRetry = 0;
    if (millis() - lastRetry > 3000) {
      lastRetry = millis();
      reconnectMqtt();
    }
  }
  mqtt.loop();
  updateLedAnimation();

  unsigned long now = millis();
  if (now - lastSampleMs >= 100) {
    lastSampleMs = now;
    sampleVibration();
  }

  if (now - lastPubMs >= PUB_INTERVAL_MS) {
    lastPubMs = now;

    float tempC = 0.0f;
    float humidPct = 0.0f;
    float pressureHpa = 1013.25f;

    if (hasHTS) {
      sensors_event_t humidity, temp;
      hts.getEvent(&humidity, &temp);
      tempC = temp.temperature;
      humidPct = humidity.relative_humidity;
    } else if (hasBMP) {
      tempC = bmp.readTemperature();
    }

    if (hasBMP) {
      pressureHpa = bmp.readPressure() / 100.0f;
    }

    JsonDocument doc;
    doc["node_id"] = DEVICE_NODE_ID;
    doc["temp"] = round(tempC * 100.0f) / 100.0f;
    doc["humid"] = round(humidPct * 100.0f) / 100.0f;
    doc["pressure"] = round(pressureHpa * 100.0f) / 100.0f;
    doc["vib_g"] = round(peakVibG * 1000.0f) / 1000.0f;
    doc["shock"] = shockFlag;
    doc["led_mode"] = currentLedMode;
    doc["uptime_sec"] = now / 1000;
    doc["scenario"] = "hardware_live";

    JsonArray sensorsArr = doc["sensors"].to<JsonArray>();
    if (hasHTS) sensorsArr.add("HTS221");
    if (hasBMP) sensorsArr.add("BMP280");
    if (hasMPU) sensorsArr.add("MPU6050");

    char payload[384];
    serializeJson(doc, payload);

    if (mqtt.connected()) {
      mqtt.publish(MQTT_TOPIC_TELEMETRY, payload);
    }
    Serial.print("[TELEMETRY] ");
    Serial.println(payload);

    // Reset vibration window
    peakVibG = 0.0f;
    shockFlag = false;
  }
}
