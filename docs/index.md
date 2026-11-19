# 🏭 AIoT for Industry — ระบบเฝ้าระวังตู้แช่ยา & ห้อง Server

<div class="hero-box">
  <h3>แพลตฟอร์มการเรียนรู้และระบบ AIoT แบบสองทางระดับอุตสาหกรรม (Full-Stack Bidirectional AIoT)</h3>
  <p>
    ผสานฮาร์ดแวร์จริง <strong>บอร์ด Cucumber RIS (ESP32-S2)</strong> อ่านเซ็นเซอร์พร้อมกัน 3 ชนิด (<strong>HTS221 + BMP280 + MPU6050</strong>) 
    ควบคุมไฟ <strong>NeoPixel RGB LED</strong> ผ่าน MQTT สองทาง ขับเคลื่อนด้วย <strong>Triple-Layer Hybrid AI</strong> 
    (Predictive Slope/Shock Engine + Local Ollama <code>qwen2.5</code> Copilot + Deterministic Safety Guardrails + Google Colab) 
    พร้อม UI ผ่าน <strong>Web Command Center & Telegram Mini App</strong>
  </p>
  <div class="hero-meta">
    <span><strong>วิชา:</strong> CN466 Internet of Things &amp; AI</span>
    <span><strong>ผู้พัฒนา:</strong> ชนาภา สดุดี (6610680214)</span>
    <a class="hero-cta" href="live_sandbox/">ทดลอง Live MQTT Sandbox →</a>
  </div>
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
  <a class="course-card" href="01_system_architecture/">
    <span class="kicker">บทที่ 01</span>
    <h4>สถาปัตยกรรมระบบ AIoT</h4>
    <p>Data Pipeline ระดับอุตสาหกรรมตั้งแต่เซ็นเซอร์ถึง AI และแอคชูเอเตอร์</p>
  </a>
  <a class="course-card" href="02_cucumber_hardware/">
    <span class="kicker">บทที่ 02</span>
    <h4>บอร์ด Cucumber RIS & Multi-Sensor</h4>
    <p>สแกน I2C (HTS221 + BMP280 + MPU6050) และคุมไฟ NeoPixel RGB LED</p>
  </a>
  <a class="course-card" href="03_mqtt_cloud_broker/">
    <span class="kicker">บทที่ 03</span>
    <h4>การสื่อสาร MQTT สองทาง</h4>
    <p>การ Publish Telemetry และ Subscribe Command บน Public Broker EMQX</p>
  </a>
  <a class="course-card" href="04_ai_anomaly_detection/">
    <span class="kicker">บทที่ 04</span>
    <h4>AI Anomaly & Google Colab</h4>
    <p>Predictive Slope, Z-Score, ETTF และ Workshop เทรน Isolation Forest vs OC-SVM</p>
  </a>
  <a class="course-card" href="05_telegram_mini_app/">
    <span class="kicker">บทที่ 05</span>
    <h4>UI, AI Copilot & Telegram Mini App</h4>
    <p>แดชบอร์ด Command Center, แชตภาษาไทยคุมบอร์ดจริง และ Telegram Bot</p>
  </a>
  <a class="course-card featured" href="live_sandbox/">
    <span class="kicker">เล่นสด · ไม่ต้องติดตั้ง</span>
    <h4>Live MQTT Sandbox (เล่นสดทันที)</h4>
    <p>ต่อ WSS ดูค่าสดจากบอร์ด Cucumber หรือทดลองจำลองวิกฤตบน GitHub Pages</p>
  </a>
</div>

### 🧑‍🏫 สำหรับผู้สอนและวิศวกร (Instructor & Engineer Track)
<div class="grid-cards">
  <a class="course-card" href="06_docker_deployment/">
    <span class="kicker">บทที่ 06</span>
    <h4>การติดตั้ง Docker & Dev Tunnels</h4>
    <p>รันระบบด้วย Docker Compose และเปิด HTTPS Port Forwarding</p>
  </a>
  <a class="course-card" href="07_business_case/">
    <span class="kicker">บทที่ 07</span>
    <h4>โมเดลธุรกิจ & ความคุ้มค่า (ROI)</h4>
    <p>B2B SaaS Cold Chain, มาตรฐาน GMP/GDP/FDA และการคำนวณจุดคุ้มทุน</p>
  </a>
  <a class="course-card" href="09_ai_safety_guardrails/">
    <span class="kicker">บทที่ 08</span>
    <h4>ความปลอดภัย AI & Guardrails</h4>
    <p>การออกแบบ Deterministic Guardrails ป้องกัน AI สั่งงานอันตรายต่อฮาร์ดแวร์</p>
  </a>
  <a class="course-card" href="08_video_walkthrough/">
    <span class="kicker">บทที่ 09</span>
    <h4>สคริปต์คลิปนำเสนอ AI Flow</h4>
    <p>แนวทางอัดคลิปส่งงาน 3–5 นาที อธิบายการสั่งงานและตรวจงานกับ AI</p>
  </a>
</div>
