---
title: หน้าแรก
hide:
  - navigation
  - toc
---

<section class="landing">
  <div class="landing-copy">
    <span class="eyebrow">วิชา: CN466 Internet of Things</span>
    <h1 class="landing-title">ระบบเฝ้าระวังตู้แช่ยาและห้อง Server ด้วย AIoT</h1>
    <p class="landing-lead">
      บทเรียนสร้างระบบ IoT ระดับอุตสาหกรรมแบบครบวงจร ตั้งแต่อ่านเซ็นเซอร์บนบอร์ด <strong>Cucumber RIS</strong>
      ส่งข้อมูลผ่าน <strong>MQTT สองทาง</strong> ให้ AI พยากรณ์ความผิดปกติล่วงหน้า
      ไปจนถึงสั่งงานอุปกรณ์จริงด้วยภาษาไทยผ่าน <strong>AI Copilot</strong> ที่มี Safety Guardrails คุ้มกัน
    </p>
    <div class="landing-cta">
      <a class="btn-primary" href="01_system_architecture/">เริ่มเรียนบทที่ 1</a>
      <a class="btn-secondary" href="live_sandbox/">เปิด Live Sandbox</a>
    </div>
    <p class="landing-byline">ผู้พัฒนา: ชนาภา สดุดี</p>
  </div>
  <div class="spec">
    <div class="spec-head"><span>System specification</span><span class="spec-live"><i></i>v2.0</span></div>
    <dl>
      <dt>Edge device</dt><dd>Cucumber RIS · ESP32-S2</dd>
      <dt>Sensors</dt><dd><code>HTS221</code> <code>BMP280</code> <code>MPU6050</code></dd>
      <dt>Actuator</dt><dd>NeoPixel RGB LED</dd>
      <dt>Transport</dt><dd>MQTT · broker.emqx.io (TCP / WSS)</dd>
      <dt>Analytics</dt><dd>Slope · Z-Score · ETTF · Shock</dd>
      <dt>Copilot</dt><dd>Gemini <code>2.5 Flash</code> + Guardrails</dd>
      <dt>Interfaces</dt><dd>Web Console · Telegram Mini App</dd>
      <dt>Compliance</dt><dd>GMP / GDP audit log (CSV)</dd>
    </dl>
  </div>
</section>

<div class="stats">
  <div><b>3</b><span>เซ็นเซอร์บนบอร์ดจริง</span></div>
  <div><b>2-way</b><span>MQTT Telemetry &amp; Command</span></div>
  <div><b>3 ชั้น</b><span>Hybrid AI + Guardrails</span></div>
  <div><b>9 บท</b><span>สำหรับผู้เรียนและผู้สอน</span></div>
</div>

## สถาปัตยกรรมระบบ

<p class="section-lead">ข้อมูลไหลจากบอร์ดผ่าน Broker เข้าสู่ AI แล้วคำสั่งที่ผ่านการตรวจสอบจะไหลกลับไปยังอุปกรณ์ — ทุกชั้นแยกจากกัน (decoupled) ผ่าน MQTT</p>

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

## เส้นทางการเรียนรู้

### สำหรับผู้เรียน (Learner Track)
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

### สำหรับผู้สอนและวิศวกร (Instructor & Engineer Track)
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
