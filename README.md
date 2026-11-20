# 🏭 AIoT Industrial Cold Chain & Sensitive Facility Monitor

[![CN466](https://img.shields.io/badge/Course-CN466_IoT_%26_AI-blue.svg)](https://github.com/chanapasadudee-max/aiot-coldchain-monitor)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-brightgreen.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-teal.svg)](https://fastapi.tiangolo.com/)
[![MQTT](https://img.shields.io/badge/MQTT-EMQX%20Broker-orange.svg)](https://www.emqx.io/)
[![Telegram](https://img.shields.io/badge/Telegram-Mini_App-2CA5E0.svg)](https://telegram.org)

> **วิชา:** CN466 Internet of Things  
> **ผู้พัฒนา:** ชนาภา สดุดี

---

## 📖 เว็บไซต์คู่มือและบทเรียน (GitHub Pages)

สามารถเข้าชมเว็บไซต์บทเรียนออนไลน์ฉบับสมบูรณ์ได้ที่:  
👉 **[เปิดดูเว็บไซต์สอน AIoT บน GitHub Pages](https://chanapasadudee-max.github.io/aiot-coldchain-monitor/)**

---

## 🌟 จุดเด่นของโปรเจกต์ (Key Features)

1. **ฮาร์ดแวร์จริง & ตัวจำลองวิกฤต:**
   - รองรับบอร์ด **Cucumber (ESP32)** ต่อเซ็นเซอร์ HTS221 ส่ง MQTT
   - มี **Industrial Simulator** จำลองสภาวะปกติ, คอมเพรสเซอร์ดับ, และประตูปิดไม่สนิท
2. **ปัญญาประดิษฐ์พยากรณ์ล่วงหน้า (Predictive AI):**
   - คำนวณ **Trend Slope** ตรวจจับอุณหภูมิไต่ขึ้นเร็วผิดปกติ *ก่อนที่ยาจะเสียหาย*
   - คำนวณเวลาที่เหลือก่อนวิกฤต (**ETTF**) และวิเคราะห์สาเหตุ (Root Cause Analysis - CAPA)
   - มีสมุดงาน **Google Colab** ให้นักเรียน/วิศวกรได้ทดลองเทรนโมเดล
3. **UI ล้ำสมัยผ่าน Telegram Mini App:**
   - Dashboard สวยงาม แสดงเกจวัด, กราฟ Real-Time, และปุ่มจำลองวิกฤต
   - เปิดผ่านแอป Telegram บนมือถือได้ทันที พร้อมระบบสั่น Haptic Feedback
4. **ความคุ้มค่าทางธุรกิจ (B2B SaaS Business Model):**
   - ป้องกันความเสียหายของยาและวัคซีนมูลค่าหลักล้านบาท ตอบโจทย์มาตรฐาน GMP / GDP / FDA

---

## 🚀 วิธีการทดสอบรันในเครื่อง (Quick Start)

### 1. ติดตั้ง Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. รันระบบ Backend & Web Dashboard (Terminal 1)
```bash
cd backend
python app.py
```
เปิดดูหน้า Dashboard ในเบราว์เซอร์ได้ที่: [http://localhost:5000](http://localhost:5000)

### 3. รันตัวจำลองเซ็นเซอร์ส่ง MQTT (Terminal 2)
```bash
cd devices/simulator
# สภาวะปกติ
python sim_industrial.py --scenario normal

# หรือจำลองวิกฤตคอมเพรสเซอร์ดับ
python sim_industrial.py --scenario failure
```

### 4. รัน Telegram Bot สำหรับรับแจ้งเตือน & เปิด Mini App (Terminal 3)
```bash
cd ui
python bot.py
```
เปิดแอป Telegram ค้นหาบอท `@Chanaps_Bot` แล้วพิมพ์ `/start`

---

## 🐳 การรันด้วย Docker Compose
```bash
docker compose up -d --build
```

---

## 📁 โครงสร้างโปรเจกต์
```text
Project_Final/
├── docs/                        # เอกสารบทเรียนสำหรับสร้าง GitHub Pages
├── mkdocs.yml                   # ไฟล์คอนฟิกเว็บไซต์เอกสาร (ธีม Material)
├── devices/
│   ├── cucumber_firmware/       # โค้ด Arduino C++ สำหรับบอร์ด Cucumber
│   └── simulator/               # sim_industrial.py (ตัวจำลองเซ็นเซอร์ระดับอุตสาหกรรม)
├── backend/
│   ├── app.py                   # FastAPI + MQTT + SQLite
│   ├── ai_engine.py             # เอนจินวิเคราะห์ความผิดปกติ (Slope + Z-Score)
│   └── incident_advisor.py      # AI สรุปสาเหตุและมาตรการแก้ไข
├── notebooks/
│   └── colab_aiot_anomaly_training.ipynb # สมุดงาน Google Colab
├── ui/
│   ├── static/index.html        # Dashboard & Telegram Mini App UI
│   └── bot.py                   # Telegram Bot (@Chanaps_Bot)
├── Dockerfile & compose.yml     # การบรรจุระบบใน Docker
├── GITHUB_DEPLOYMENT_GUIDE.md   # คู่มือการนำขึ้น GitHub Pages
└── README.md
```
