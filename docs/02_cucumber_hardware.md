# บทที่ 2: บอร์ด Cucumber & เซ็นเซอร์ (Hardware & Firmware)

> คู่มือการต่อวงจรบอร์ด Cucumber (ESP32) เพื่อส่งข้อมูลอุณหภูมิและความชื้นเข้าสู่ระบบ หรือการใช้งาน Industrial Simulator

---

## 2.1 บอร์ด Cucumber (ESP32) คืออะไร?

**บอร์ด Cucumber** เป็นบอร์ดไมโครคอนโทรลเลอร์ที่ใช้ชิปประมวลผล **ESP32** (Dual-core Xtensa 32-bit LX6) ซึ่งมีคุณสมบัติโดดเด่นสำหรับงาน IoT:
- มีโมดูล **Wi-Fi 802.11 b/g/n (2.4 GHz)** และ Bluetooth ในตัว
- รองรับการเชื่อมต่อเซ็นเซอร์ผ่าน I2C, SPI, UART และขา Analog/Digital หลากหลาย
- ใช้พลังงานต่ำ เหมาะสำหรับการติดตั้งประจำตู้แช่หรือแร็คเซิร์ฟเวอร์

---

## 2.2 การต่อวงจรเซ็นเซอร์ HTS221 กับบอร์ด Cucumber

เซ็นเซอร์ **HTS221** เป็นเซ็นเซอร์วัดอุณหภูมิและความชื้นความแม่นยำสูง เชื่อมต่อผ่านบัส **I2C**:

| ขาของเซ็นเซอร์ HTS221 | ขาบนบอร์ด Cucumber (ESP32) | คำอธิบาย |
|:---:|:---:|---|
| **VCC** | 3.3V | แหล่งจ่ายไฟบวก 3.3 โวลต์ |
| **GND** | GND | กราวด์ร่วม |
| **SDA** | GPIO 21 (SDA) | สายรับส่งข้อมูลข้อมูล I2C |
| **SCL** | GPIO 22 (SCL) | สายสัญญาณนาฬิกา I2C |

> [!WARNING]
> ห้ามต่อขา VCC ของเซ็นเซอร์เข้ากับ 5V เพราะอาจทำให้วงจรภายในเซ็นเซอร์เสียหายได้

---

## 2.3 โค้ดเฟิร์มแวร์ Arduino C++ สำหรับบอร์ด Cucumber

ซอร์สโค้ดฉบับเต็มอยู่ที่ไฟล์ `devices/cucumber_firmware/cucumber_firmware.ino`

```cpp
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* mqtt_server = "broker.emqx.io";
const int mqtt_port = 1883;
const char* mqtt_topic = "tse/cn466/chanapa/telemetry";

WiFiClient espClient;
PubSubClient client(espClient);

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  client.setServer(mqtt_server, mqtt_port);
}

void loop() {
  if (!client.connected()) reconnect();
  client.loop();

  // อ่านค่าเซ็นเซอร์และส่ง JSON ทุก 2 วินาที
  StaticJsonDocument<200> doc;
  doc["node_id"] = "cucumber-01";
  doc["temp"] = 4.25;
  doc["humid"] = 62.10;
  
  char buffer[256];
  serializeJson(doc, buffer);
  client.publish(mqtt_topic, buffer);
  delay(2000);
}
```

---

## 2.4 กรณีไม่มีบอร์ดจริง? ใช้ Industrial Simulator

ในกรณีที่ไม่มีบอร์ดจริงหรือต้องการทดสอบจำลองวิกฤต เช่น คอมเพรสเซอร์ดับหรือประตูตู้แช่เปิดทิ้งไว้ สามารถรันสคริปต์จำลองบนคอมพิวเตอร์ได้ทันที:

```bash
# ติดตั้งไลบรารี
pip install paho-mqtt

# รันโหมดปกติ (สภาวะตู้แช่ยา 2-6°C)
python devices/simulator/sim_industrial.py --scenario normal

# รันโหมดวิกฤต (จำลองคอมเพรสเซอร์ดับ อุณหภูมิไต่ขึ้นเร็ว)
python devices/simulator/sim_industrial.py --scenario failure

# รันโหมดลืมปิดประตูตู้แช่
python devices/simulator/sim_industrial.py --scenario door_ajar
```
