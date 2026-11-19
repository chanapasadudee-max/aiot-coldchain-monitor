# 🏭 AIoT for Industry — ระบบเฝ้าระวังตู้แช่ยา & ห้อง Server

<div class="hero-box">
  <h3>🌟 แพลตฟอร์มการเรียนรู้และระบบ AIoT แบบสองทางระดับอุตสาหกรรม (Full-Stack Bidirectional AIoT)</h3>
  <p>
    ผสานฮาร์ดแวร์จริง <strong>บอร์ด Cucumber RIS (ESP32-S2)</strong> อ่านเซ็นเซอร์พร้อมกัน 3 ชนิด (<strong>HTS221 + BMP280 + MPU6050</strong>) 
    ควบคุมไฟ <strong>NeoPixel RGB LED</strong> ผ่าน MQTT สองทาง ขับเคลื่อนด้วย <strong>Triple-Layer Hybrid AI</strong> 
    (Predictive Slope/Shock Engine + Local Ollama <code>qwen2.5</code> Copilot + Deterministic Safety Guardrails + Google Colab) 
    พร้อม UI ผ่าน <strong>Web Command Center & Telegram Mini App</strong>
  </p>
  <p style="margin-bottom: 0; font-size: 0.85rem; opacity: 0.88;">
    <strong>วิชา:</strong> CN466 Project - Internet of Things & AI | <strong>ผู้พัฒนา:</strong> ชนาภา สดุดี (6610680214)<br>
    👉 <a href="live_sandbox/"><strong>คลิกทดลองเล่น Live MQTT Sandbox สดบนหน้าเว็บได้เลย!</strong></a>
  </p>
</div>

---

## 📐 แผนภาพสถาปัตยกรรมระบบ (System Architecture)

```mermaid
flowchart TD
    subgraph IOT ["1. Cucumber RIS (ESP32-S2) — Multi-Sensor + Actuator"]
        S["HTS221 (Temp/Humid)<br>BMP280 (Pressure)<br>MPU6050 (Vibration/Shock)"] --> MCU["ESP32-S2<br>PlatformIO C++"]
        MCU --> LED["NeoPixel RGB LED<br>(GPIO 18)"]
    end

    subgraph CLOUD ["2. Cloud MQTT Broker & FastAPI Gateway"]
        BROKER["broker.emqx.io<br>TX: telemetry | RX: cmd"]
        API["FastAPI + SQLite + GMP CSV"]
    end

    subgraph AI ["3. Triple-Layer Hybrid AI"]
        L1["Layer 1: Anomaly Engine<br>(Slope, Z-Score, ETTF, Shock)"]
        L2["Layer 2: Local Ollama qwen2.5<br>Thai Copilot + 🛡️ Safety Guardrails"]
        L3["Layer 3: Google Colab<br>(Isolation Forest vs One-Class SVM)"]
    end

    subgraph UI ["4. User Interface & Learning Platform"]
        WEB["Web Command Center /<br>Telegram Mini App"]
        BOT["Telegram Bot (@Chanaps_Bot)"]
        GHP["GitHub Pages Docs +<br>Live WSS Sandbox"]
    end

    MCU -- "Publish JSON" --> BROKER --> API
    API --> L1 --> L2
    L2 -- "Validated CMD" --> BROKER -- "Subscribe" --> MCU
    API <--> WEB
    API <--> BOT
    BROKER -. "WSS :8084" .-> GHP
```

---

## 📚 เส้นทางการเรียนรู้ (แบ่งแทร็กตามบทบาท)

### 🎓 สำหรับผู้เรียน (Learner Track)
<div class="grid-cards">
  <div class="course-card">
    <h4><a href="01_system_architecture/">บทที่ 1: สถาปัตยกรรมระบบ AIoT</a></h4>
    <p>Data Pipeline ระดับอุตสาหกรรมตั้งแต่เซ็นเซอร์ถึง AI และแอคชูเอเตอร์</p>
  </div>
  <div class="course-card">
    <h4><a href="02_cucumber_hardware/">บทที่ 2: บอร์ด Cucumber RIS & Multi-Sensor</a></h4>
    <p>สแกน I2C (HTS221 + BMP280 + MPU6050) และคุมไฟ NeoPixel RGB LED</p>
  </div>
  <div class="course-card">
    <h4><a href="03_mqtt_cloud_broker/">บทที่ 3: การสื่อสาร MQTT สองทาง</a></h4>
    <p>การ Publish Telemetry และ Subscribe Command บน Public Broker EMQX</p>
  </div>
  <div class="course-card">
    <h4><a href="04_ai_anomaly_detection/">บทที่ 4: AI Anomaly & Google Colab</a></h4>
    <p>Predictive Slope, Z-Score, ETTF และ Workshop เทรน Isolation Forest vs OC-SVM</p>
  </div>
  <div class="course-card">
    <h4><a href="05_telegram_mini_app/">บทที่ 5: UI, AI Copilot & Telegram Mini App</a></h4>
    <p>แดชบอร์ด Command Center, แชตภาษาไทยคุมบอร์ดจริง และ Telegram Bot</p>
  </div>
  <div class="course-card">
    <h4><a href="live_sandbox/">🧪 Live MQTT Sandbox (เล่นสดทันที)</a></h4>
    <p>ต่อ WSS ดูค่าสดจากบอร์ด Cucumber หรือทดลองจำลองวิกฤตบน GitHub Pages</p>
  </div>
</div>

### 🧑‍🏫 สำหรับผู้สอนและวิศวกร (Instructor & Engineer Track)
<div class="grid-cards">
  <div class="course-card">
    <h4><a href="06_docker_deployment/">บทที่ 6: การติดตั้ง Docker & Dev Tunnels</a></h4>
    <p>รันระบบด้วย Docker Compose และเปิด HTTPS Port Forwarding</p>
  </div>
  <div class="course-card">
    <h4><a href="07_business_case/">บทที่ 7: โมเดลธุรกิจ & ความคุ้มค่า (ROI)</a></h4>
    <p>B2B SaaS Cold Chain, มาตรฐาน GMP/GDP/FDA และการคำนวณจุดคุ้มทุน</p>
  </div>
  <div class="course-card">
    <h4><a href="09_ai_safety_guardrails/">บทที่ 8: ความปลอดภัย AI & Guardrails</a></h4>
    <p>การออกแบบ Deterministic Guardrails ป้องกัน AI สั่งงานอันตรายต่อฮาร์ดแวร์</p>
  </div>
  <div class="course-card">
    <h4><a href="08_video_walkthrough/">บทที่ 9: สคริปต์คลิปนำเสนอ AI Flow</a></h4>
    <p>แนวทางอัดคลิปส่งงาน 3–5 นาที อธิบายการสั่งงานและตรวจงานกับ AI</p>
  </div>
</div>
