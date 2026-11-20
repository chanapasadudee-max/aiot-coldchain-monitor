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

<div class="flow">
  <ol class="flow-steps">
    <li class="flow-step">
      <span class="flow-num">01</span>
      <span class="flow-kicker">อุปกรณ์</span>
      <h3>บอร์ด Cucumber RIS</h3>
      <p>อ่านอุณหภูมิ ความชื้น ความดัน และแรงสั่น แล้วส่งเป็น JSON ทุก 2 วินาที</p>
      <div class="flow-tags"><code>HTS221</code><code>BMP280</code><code>MPU6050</code></div>
    </li>
    <li class="flow-step">
      <span class="flow-num">02</span>
      <span class="flow-kicker">สื่อสาร</span>
      <h3>MQTT Broker</h3>
      <p>ตัวกลางรับ–ส่งข้อความ ทำให้บอร์ดกับแอปไม่ต้องเชื่อมกันโดยตรง</p>
      <div class="flow-tags"><code>broker.emqx.io</code><code>…/telemetry</code><code>…/cmd</code></div>
    </li>
    <li class="flow-step">
      <span class="flow-num">03</span>
      <span class="flow-kicker">วิเคราะห์</span>
      <h3>AI Engine + Copilot</h3>
      <p>จับความผิดปกติก่อนเกินเกณฑ์ และแปลคำสั่งภาษาไทยเป็นการสั่งงานอุปกรณ์</p>
      <div class="flow-tags"><code>Slope</code><code>Z-Score</code><code>ETTF</code><code>Gemini</code></div>
    </li>
    <li class="flow-step">
      <span class="flow-num">04</span>
      <span class="flow-kicker">ผู้ใช้</span>
      <h3>หน้าจอ &amp; การแจ้งเตือน</h3>
      <p>Dashboard, Telegram Mini App / Bot และ Live Sandbox บนเว็บนี้</p>
      <div class="flow-tags"><code>Web</code><code>Telegram</code><code>GitHub Pages</code></div>
    </li>
  </ol>
  <div class="flow-return">
    <span class="flow-return-line" aria-hidden="true"></span>
    <p><b>ขากลับ:</b> คำสั่งเปลี่ยนไฟ LED จาก AI หรือผู้ใช้ ต้องผ่าน <b>Safety Guardrails</b> ก่อน แล้วจึงส่งผ่าน Broker กลับไปที่บอร์ด</p>
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
