# บทที่ 1: สถาปัตยกรรมระบบ (System Architecture)

> เรียนรู้การออกแบบระบบ IoT และ AI แบบ End-to-End เพื่อรองรับสภาพแวดล้อมที่ต้องการความเสถียร 24 ชั่วโมงต่อวัน

---

## 1.1 ปรัชญาการออกแบบระดับอุตสาหกรรม (Industrial IoT Principles)

ในงานระดับผู้บริโภคทั่วไป (Consumer IoT) เซ็นเซอร์อาจหลุดหรือหน่วงได้โดยไม่ส่งผลร้ายแรง แต่ในระบบ **Cold Chain และ Data Center** การออกแบบต้องยึดหลักสำคัญ 3 ประการ:

1. **High Reliability & Low Latency:** ข้อมูลต้องส่งถึงคลาวด์ภายในไม่เกิน 2–3 วินาที เพื่อให้ระบบตรวจจับการเปลี่ยนแปลงของอุณหภูมิได้อย่างทันท่วงที
2. **Predictive Alerting over Threshold Alerting:** หากรอให้อุณหภูมิเกิน 8°C แล้วค่อยแจ้งเตือน สินค้าในตู้แช่อาจเริ่มเสื่อมสภาพแล้ว ระบบที่ดีต้อง **พยากรณ์ล่วงหน้า (Predictive Warning)** จากอัตราการไต่ขึ้นของความชัน (Trend Slope)
3. **Decoupled Architecture:** อุปกรณ์ภาคสนาม (บอร์ด Cucumber) ไม่ควรเชื่อมต่อกับหน้าเว็บหรือแอปพลิเคชันโดยตรง แต่ควรผ่าน Message Broker (MQTT) เพื่อความปลอดภัยและการขยายตัว (Scalability)

---

## 1.2 โครงสร้างข้อมูลและการเดินทางของข้อมูล (Data Pipeline)

```mermaid
%%{init: {"themeVariables": {"actorLineColor": "#b9bec7", "signalColor": "#8a909b"}}}%%
sequenceDiagram
    autonumber
    participant C as บอร์ด
    participant M as Broker
    participant B as Backend
    participant AI as AI
    participant U as ผู้ใช้

    C->>M: ส่ง JSON ทุก 2 วินาที
    M->>B: ส่งต่อข้อความ
    B->>AI: วิเคราะห์ค่าล่าสุด
    AI-->>B: ระดับความเสี่ยง + ETTF
    Note over B: บันทึกลง SQLite
    alt WARNING หรือ CRITICAL
        B->>U: แจ้งเตือน Telegram + CAPA
    end
    U->>B: สั่งงาน เช่น "เปิดไฟแดง"
    B->>AI: ตรวจด้วย Guardrails
    AI-->>B: อนุญาต / ปฏิเสธ
    B->>M: ส่งคำสั่งที่อนุญาต
    M->>C: เปลี่ยนสีไฟ LED
```

<div class="seq-legend">
  <p><span class="seq-badge">1–4</span><b>ขาไป</b> บอร์ดส่งค่าเซ็นเซอร์ผ่าน Broker ให้ Backend ซึ่งส่งต่อให้ AI ประเมินความเสี่ยง แล้วบันทึกทุกค่าลงฐานข้อมูล</p>
  <p><span class="seq-badge">5</span><b>แจ้งเตือน</b> เกิดเฉพาะเมื่อ AI ประเมินว่าเป็น WARNING หรือ CRITICAL โดยส่งเข้า Telegram พร้อมคำแนะนำ CAPA</p>
  <p><span class="seq-badge">6–10</span><b>ขากลับ</b> คำสั่งจากผู้ใช้ต้องผ่าน Safety Guardrails ก่อนเสมอ ถ้าอนุญาตจึงส่งผ่าน Broker ไปเปลี่ยนไฟบนบอร์ด</p>
</div>

รายละเอียดเทคโนโลยีของแต่ละส่วนอยู่ในตารางหัวข้อ 1.3 ด้านล่าง

---

## 1.3 ส่วนประกอบหลักของระบบ (System Components)

| ชั้นการทำงาน | เทคโนโลยีที่ใช้ | หน้าที่หลัก |
|---|---|---|
| **ฮาร์ดแวร์ IoT** | บอร์ด Cucumber (ESP32) + HTS221 | เก็บข้อมูลอุณหภูมิและความชื้น แปลงเป็น JSON |
| **ตัวจำลอง (Simulator)** | Python 3 + `paho-mqtt` | จำลองสภาวะปกติ, คอมเพรสเซอร์ดับ, ประตูเปิดค้าง |
| **เครือข่ายสื่อสาร** | MQTT (TCP/IP Port 1883) | สื่อสารข้อมูลน้ำหนักเบาและประหยัดแบนด์วิดท์ |
| **เซิร์ฟเวอร์ Backend** | FastAPI + Uvicorn | รับข้อมูล, บันทึกฐานข้อมูล SQLite, บริการ REST API |
| **เอนจิน AI** | Scikit-learn + Heuristic Slope | วิเคราะห์ความชัน, คำนวณ Z-Score, ประเมิน ETTF |
| **ส่วนติดต่อผู้ใช้ (UI)** | HTML5, CSS3, JS, Chart.js | แสดงเกจวัด, กราฟแนวโน้ม, รองรับ Telegram SDK |
| **ช่องทางแจ้งเตือน** | Telegram Bot API | ยิงแจ้งเตือนเหตุด่วนเข้าสมาร์ตโฟนของวิศวกร |
