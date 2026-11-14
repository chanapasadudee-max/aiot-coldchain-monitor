# บทที่ 3: การสื่อสารผ่าน MQTT Broker (Cloud Communication)

> ทำความเข้าใจโพรโทคอล MQTT และการจัดโครงสร้าง Payload JSON สำหรับส่งข้อมูล Telemetry สู่ Cloud

---

## 3.1 ทำไมงาน IoT อุตสาหกรรมจึงเลือกใช้ MQTT แทน HTTP?

แม้ว่า HTTP REST API จะเป็นที่นิยมในการพัฒนาเว็บทั่วไป แต่สำหรับงานอุปกรณ์ฝังตัว (Embedded IoT) โพรโทคอล **MQTT (Message Queuing Telemetry Transport)** มีข้อได้เปรียบที่สำคัญ:

1. **Lightweight Header:** ส่วนหัวของแพ็กเก็ต MQTT มีขนาดเล็กเพียง **2 Bytes** (เทียบกับ HTTP ที่มี Header ขนาดหลายร้อยไบต์) จึงประหยัดแบนด์วิดท์อย่างมาก
2. **Publish / Subscribe Model:** บอร์ด Cucumber ไม่จำเป็นต้องรู้ว่ามีใครกำลังดูหน้าจออยู่ แค่ส่งข้อมูล (Publish) ขึ้นไปยังหัวข้อ (Topic) ที่กำหนด จากนั้นระบบ Backend หรือ Dashboard จะมารับฟัง (Subscribe) เอง
3. **Keep-Alive & Fast Reconnect:** มีกลไกตรวจสอบสถานะการเชื่อมต่อตลอดเวลา หากสายสัญญาณ Wi-Fi หลุด ระบบจะต่อให้อัตโนมัติทันทีที่สัญญาณกลับมา

---

## 3.2 การตั้งค่า MQTT Broker ในโครงการ

โครงการนี้ใช้บริการ **Public MQTT Broker** ของ EMQX:

- **Broker Address:** `broker.emqx.io`
- **TCP Port (สำหรับบอร์ด IoT):** `1883`
- **WebSocket Port (WSS สำหรับเว็บ):** `8084`
- **หัวข้อหลัก (Topic):** `tse/cn466/chanapa/telemetry`

---

## 3.3 โครงสร้างข้อความ Telemetry (JSON Schema)

ข้อมูลที่ส่งขึ้น MQTT Broker ถูกจัดในรูปแบบ JSON มาตรฐาน เพื่อให้ง่ายต่อการแปลงและนำไปวิเคราะห์ต่อด้วย AI:

```json
{
  "node_id": "cucumber-coldchain-01",
  "ts": "2026-11-14T08:15:30.123456Z",
  "temp": 4.35,
  "humid": 61.2,
  "status": "NORMAL",
  "scenario": "live"
}
```

### คำอธิบายฟิลด์ข้อมูล:
- `node_id`: รหัสประจำจุดตรวจวัด (เช่น ตู้แช่ที่ 1, แร็คเซิร์ฟเวอร์แถว A)
- `ts`: เวลาตามมาตรฐาน ISO 8601 UTC
- `temp`: ค่าอุณหภูมิที่วัดได้ หน่วยเป็นองศาเซลเซียส (°C)
- `humid`: ค่าความชื้นสัมพัทธ์ในอากาศ หน่วยเป็นเปอร์เซ็นต์ (%RH)
- `scenario`: ป้ายกำกับสภาวะการทำงาน (เช่น live, normal, failure)
