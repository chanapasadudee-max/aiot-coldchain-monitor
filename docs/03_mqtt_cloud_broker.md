# บทที่ 3: การสื่อสาร MQTT สองทาง (Bidirectional MQTT & Cloud Broker)

> ทำความเข้าใจโพรโทคอล MQTT แบบสื่อสารสองทาง: บอร์ดส่งข้อมูล Multi-Sensor ขึ้น Cloud และรับคำสั่งควบคุมไฟ RGB LED กลับจาก AI

---

## 3.1 ทำไมงาน IoT อุตสาหกรรมจึงเลือกใช้ MQTT แทน HTTP?

1. **Lightweight Header:** ส่วนหัวของแพ็กเก็ต MQTT มีขนาดเล็กเพียง **2 Bytes** ประหยัดแบนด์วิดท์และพลังงาน
2. **Publish / Subscribe Model:** แยกผู้ส่ง (บอร์ด Cucumber RIS) ออกจากผู้รับ (Backend / Dashboard / Live Sandbox) ทำให้ขยายจำนวนอุปกรณ์ได้ง่าย
3. **Bidirectional Control:** บอร์ดสามารถ Subscribe หัวข้อคำสั่ง (`.../cmd`) เพื่อรับคำสั่งเปลี่ยนสีไฟหรือโหมดการทำงานได้ภายในไม่กี่มิลลิวินาที

---

## 3.2 การตั้งค่า MQTT Broker & Topics ในโครงการ

- **Broker Address:** `broker.emqx.io`
- **TCP Port (สำหรับบอร์ด Cucumber RIS & Python):** `1883`
- **Secure WebSocket Port (WSS สำหรับเบราว์เซอร์ & GitHub Pages):** `8084` (`wss://broker.emqx.io:8084/mqtt`)

| ทิศทาง | MQTT Topic | คำอธิบาย |
|---|---|---|
| **Uplink (Telemetry)** | `tse/cn466/chanapa/telemetry` | บอร์ด Cucumber RIS ส่งค่า HTS221 + BMP280 + MPU6050 ทุก 2 วินาที |
| **Uplink (Legacy)** | `tse/cn466/chanapa` | รองรับเฟิร์มแวร์ Lab 7 เดิม (Temp/Humid) ย้อนหลังได้ 100% |
| **Downlink (Command)** | `tse/cn466/chanapa/cmd` | Backend / AI Copilot ส่งคำสั่งควบคุมไฟ NeoPixel RGB LED กลับไปยังบอร์ด |

---

## 3.3 โครงสร้าง JSON Telemetry (Uplink)

```json
{
  "node_id": "cucumber-ris-01",
  "temp": 30.51,
  "humid": 47.16,
  "pressure": 1013.46,
  "vib_g": 0.109,
  "shock": false,
  "led_mode": "safe",
  "uptime_sec": 124,
  "sensors": ["HTS221", "BMP280", "MPU6050"],
  "scenario": "hardware_live"
}
```

## 3.4 โครงสร้าง JSON Command (Downlink)

```json
{
  "cmd": "set_led",
  "mode": "critical",
  "r": 255,
  "g": 0,
  "b": 20
}
```
- `mode`: `"safe"` (เขียว), `"warning"` (เหลืองทอง), `"critical"` (แดงกระพริบ), `"off"` (ปิดไฟ), `"custom"` (ระบุค่า RGB เอง)
- `{"cmd": "ping"}`: สั่งบอร์ดตอบกลับสถานะความพร้อม (`ack: "pong"`)
