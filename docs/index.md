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

<div class="arch">
  <div class="arch-legend">
    <span><i class="lg up"></i>Telemetry (บอร์ด → AI)</span>
    <span><i class="lg down"></i>Command (AI → บอร์ด) ผ่าน Guardrails</span>
    <span><i class="lg wss"></i>WSS ตรงจากเบราว์เซอร์</span>
  </div>
  <div class="arch-row">
    <div class="arch-lane">
      <span class="arch-kicker">01 · EDGE</span>
      <strong>Cucumber RIS</strong>
      <span class="arch-sub">ESP32-S2 · PlatformIO C++</span>
    </div>
    <div class="arch-nodes">
      <div class="arch-node"><b>เซ็นเซอร์ 3 ชนิด</b><span class="chips"><code>HTS221</code><code>BMP280</code><code>MPU6050</code></span><small>อุณหภูมิ/ความชื้น · ความดัน · แรงสั่น</small></div>
      <div class="arch-node"><b>ESP32-S2 MCU</b><small>อ่าน I2C → แพ็ก JSON → Publish</small></div>
      <div class="arch-node act"><b>NeoPixel RGB LED</b><small>Actuator · GPIO 18</small></div>
    </div>
  </div>
  <div class="arch-link">
    <span class="flow up">Publish JSON</span>
    <span class="flow down">Subscribe CMD</span>
  </div>
  <div class="arch-row">
    <div class="arch-lane">
      <span class="arch-kicker">02 · TRANSPORT</span>
      <strong>MQTT Broker</strong>
      <span class="arch-sub">broker.emqx.io · <code>tse/cn466/chanapa/</code></span>
    </div>
    <div class="arch-nodes">
      <div class="arch-node"><b>TX · Telemetry</b><small><code>…/telemetry</code> บอร์ด → คลาวด์</small></div>
      <div class="arch-node"><b>RX · Command</b><small><code>…/cmd</code> คลาวด์ → บอร์ด</small></div>
      <div class="arch-node wss"><b>WebSocket</b><small>พอร์ต <code>8084</code> สำหรับเบราว์เซอร์</small></div>
    </div>
  </div>
  <div class="arch-link">
    <span class="flow up">Telemetry</span>
    <span class="flow down">Validated CMD</span>
  </div>
  <div class="arch-row">
    <div class="arch-lane">
      <span class="arch-kicker">03 · INTELLIGENCE</span>
      <strong>Triple-Layer Hybrid AI</strong>
      <span class="arch-sub">FastAPI + SQLite + GMP CSV</span>
    </div>
    <div class="arch-nodes">
      <div class="arch-node"><b>L1 · Anomaly Engine</b><small>Slope · Z-Score · ETTF · Shock</small></div>
      <div class="arch-node ai"><b>L2 · Ollama <code>qwen2.5</code></b><small>Thai Copilot สั่งงานด้วยภาษาไทย</small></div>
      <div class="arch-node guard"><b>🛡️ Safety Guardrails</b><small>Deterministic · บล็อกคำสั่งอันตราย</small></div>
      <div class="arch-node offline"><b>L3 · Google Colab</b><small>Isolation Forest vs One-Class SVM (เทรนออฟไลน์)</small></div>
    </div>
  </div>
  <div class="arch-link">
    <span class="flow up">REST API</span>
    <span class="flow down">คำสั่งจากผู้ใช้</span>
    <span class="flow wss">WSS :8084</span>
  </div>
  <div class="arch-row">
    <div class="arch-lane">
      <span class="arch-kicker">04 · INTERFACE</span>
      <strong>ผู้ใช้ &amp; ผู้เรียน</strong>
      <span class="arch-sub">เว็บ · มือถือ · เอกสาร</span>
    </div>
    <div class="arch-nodes">
      <div class="arch-node"><b>Web Command Center</b><small>+ Telegram Mini App</small></div>
      <div class="arch-node"><b>Telegram Bot</b><small>@Chanaps_Bot · แจ้งเตือน CAPA</small></div>
      <div class="arch-node wss"><b>GitHub Pages</b><small>เว็บสอน + Live MQTT Sandbox</small></div>
    </div>
  </div>
</div>

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
