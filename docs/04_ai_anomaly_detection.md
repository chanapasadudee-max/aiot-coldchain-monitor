# บทที่ 4: ปัญญาประดิษฐ์ตรวจจับวิกฤต (AI Anomaly Detection)

> หัวใจสำคัญของ AIoT: การเปลี่ยนจาก "ระบบดูย้อนหลัง" สู่ "ระบบพยากรณ์ล่วงหน้าก่อนของเสียหาย"

---

## 4.1 ขีดจำกัดของระบบแจ้งเตือนแบบเดิม (Rule-Based vs AIoT)

ในระบบเฝ้าระวังตู้แช่ยุคเก่า มักใช้กฎแบบพื้นฐาน (Hard Threshold):
$$\text{IF } \text{Temp} > 8.0^\circ\text{C} \implies \text{TRIGGER ALARM}$$

**ปัญหาของวิธีนี้คืออะไร?**
เมื่ออุณหภูมิแตะ 8.1°C นั่นแปลว่า **ระบบทำความเย็นดับไปแล้วเป็นเวลา 20–30 นาที!** ความเย็นเริ่มระเหย และยาปฏิชีวนะหรือวัคซีนอาจเสื่อมสภาพไปแล้วบางส่วน

**แนวทางของระบบ AIoT ในโปรเจกต์นี้:**
เรานำ AI เข้ามาวิเคราะห์ **"ความชันของการเปลี่ยนแปลง (Trend Slope)"** ร่วมกับ **"ค่าเบี่ยงเบนทางสถิติ (Z-Score)"**:
หากอุณหภูมิปัจจุบันยังอยู่ที่ 5.5°C (ยังไม่เกิน 8°C) แต่อุณหภูมิไต่ขึ้นเร็วต่อเนื่อง $0.3^\circ\text{C}$ ทุกๆ 2 วินาที **AI จะส่งสัญญาณ PREDICTIVE WARNING ทันที** พร้อมประเมินเวลาที่เหลือก่อนวิกฤต (ETTF)

---

## 4.2 สถาปัตยกรรมโมเดล AI (Hybrid AI Architecture)

ระบบประกอบด้วยโมเดล 2 ระดับ:

```mermaid
flowchart LR
    A["ข้อมูล Telemetry<br>(Temp, Humid)"] --> B["Feature Engineering<br>(Rolling Mean, Z-Score, Slope)"]
    B --> C["1. Fast Edge Engine<br>(Z-Score & Linear Slope)"]
    B --> D["2. ML Isolation Forest<br>(เทรนบน Google Colab)"]
    C --> E["ประเมิน Risk Level<br>(NORMAL / WARNING / CRITICAL)"]
    D --> E
    E --> F["AI Incident Advisor<br>(สรุปสาเหตุ & แนะนำ CAPA)"]
```

### 1. Rolling Linear Slope Formula
คำนวณความชันจากชุดข้อมูล $N$ จุดล่าสุด ($N=15$):

$$\text{Slope} = \frac{\sum (x_i - \bar{x})(y_i - \bar{y})}{\sum (x_i - \bar{x})^2}$$

- $\text{Slope} \le 0.05$: สภาวะปกติ ความเย็นคงที่
- $\text{Slope} > 0.15$: **วิกฤตแฝง!** คอมเพรสเซอร์หยุดทำงาน หรือประตูปิดไม่สนิท

### 2. Statistical Z-Score
$$Z = \frac{\text{Temp} - \mu}{\sigma}$$
ตรวจจับกรณีเซ็นเซอร์เสีย (Sensor Glitch) หรือมีคลื่นแม่เหล็กรบกวนกะทันหัน

### 3. Estimated Time to Failure (ETTF)
พยากรณ์เวลาที่เหลือก่อนสินค้าจะเสียหาย:
$$\text{ETTF} = \frac{T_{\text{max}} - T_{\text{current}}}{\text{Slope}} \times \Delta t$$

---

## 4.3 การทดลองบน Google Colab (Hands-on Notebook)

เราได้เตรียมสมุดงาน **Jupyter Notebook** อยู่ที่:
`notebooks/colab_aiot_anomaly_training.ipynb`

### สิ่งที่ผู้เรียนจะได้ทดลองใน Colab:
1. โหลดข้อมูลจำลอง 600 วินาทีที่มีทั้งช่วงปกติและช่วงตู้แช่ดับ
2. เขียนโค้ดสกัด Features ด้วย Pandas
3. เทรนโมเดล **Isolation Forest** ด้วย Scikit-learn
4. พล็อตกราฟ Scatter Plot ไฮไลต์จุดที่ AI ชี้ว่าเป็นความผิดปกติ
