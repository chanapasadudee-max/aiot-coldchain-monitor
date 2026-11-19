# 🧪 Live MQTT Sandbox (ทดลองเล่นสดบน GitHub Pages)

> หน้านี้เชื่อมต่อกับ **MQTT Broker สาธารณะ (`wss://broker.emqx.io:8084/mqtt`)** โดยตรงจากเบราว์เซอร์ของคุณ (และรองรับ **Telegram Mini App** ตลอด 24 ชม.)!  
> สามารถดูข้อมูลสดจากบอร์ด **Cucumber RIS (HTS221 + BMP280 + MPU6050)** หรือกดปุ่ม **จำลองวิกฤต (Virtual Simulator)** ได้ทันทีโดยไม่ต้องเปิดเซิร์ฟเวอร์ในเครื่อง

<div id="sandbox-root">
  <div class="sb-bar">
    <span id="sb-conn" class="sb-conn">⏳ กำลังเชื่อมต่อ WSS broker.emqx.io:8084...</span>
    <span class="sb-topic">Topic: <code>tse/cn466/chanapa/telemetry</code></span>
    <div class="sb-actions">
      <button onclick="sbToggleSim()" id="sb-sim-btn" class="sb-btn primary">▶️ เริ่มโหมดจำลอง (Offline Demo)</button>
      <button onclick="sbSendLed('safe')" class="sb-btn"><span class="sb-led g"></span>ไฟเขียว</button>
      <button onclick="sbSendLed('warning')" class="sb-btn"><span class="sb-led y"></span>ไฟเหลือง</button>
      <button onclick="sbSendLed('critical')" class="sb-btn"><span class="sb-led r"></span>ไฟแดง</button>
    </div>
  </div>

  <div class="sb-grid">
    <div class="sb-tile">
      <div class="sb-label">อุณหภูมิ<small>HTS221</small></div>
      <div id="sb-temp" class="sb-val temp">-- °C</div>
    </div>
    <div class="sb-tile">
      <div class="sb-label">ความชื้น<small>HTS221</small></div>
      <div id="sb-humid" class="sb-val humid">-- %</div>
    </div>
    <div class="sb-tile">
      <div class="sb-label">ความดัน<small>BMP280</small></div>
      <div id="sb-press" class="sb-val">-- hPa</div>
    </div>
    <div class="sb-tile">
      <div class="sb-label">แรงสั่น<small>MPU6050</small></div>
      <div id="sb-vib" class="sb-val vib">-- g</div>
    </div>
  </div>

  <div class="sb-chart">
    <canvas id="sbChart"></canvas>
  </div>

  <pre id="sb-raw" class="sb-raw">กำลังรอรับข้อความ JSON จากบอร์ด Cucumber...</pre>
</div>

<script src="https://telegram.org/js/telegram-web-app.js"></script>
<script src="https://unpkg.com/mqtt@5.10.1/dist/mqtt.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<script>
(function() {
  // Telegram Mini App SDK (works 24/7 directly from GitHub Pages HTTPS!)
  const tg = window.Telegram?.WebApp;
  if (tg) { tg.ready(); tg.expand(); }
  const haptic = (t = 'medium') => tg?.HapticFeedback?.impactOccurred?.(t);

  const ctx = document.getElementById('sbChart').getContext('2d');
  const v = (n) => getComputedStyle(document.body).getPropertyValue(n).trim();
  const areaFill = () => document.body.getAttribute('data-md-color-scheme') === 'default' ? 'rgba(140,24,28,0.12)' : 'rgba(233,185,73,0.14)';
  const sbChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: [],
      datasets: [
        { label: 'Temperature (°C)', data: [], borderColor: v('--x-accent'), backgroundColor: areaFill(), fill: true, tension: 0.35, borderWidth: 2, pointRadius: 0 }
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      scales: {
        x: { grid: { display: false }, ticks: { color: v('--md-default-fg-color--light'), font: { size: 10 }, maxRotation: 0 } },
        y: { ticks: { color: v('--md-default-fg-color--light'), font: { size: 10 } }, grid: { color: v('--x-border') } }
      },
      plugins: { legend: { display: false } }
    }
  });
  new MutationObserver(() => {
    sbChart.data.datasets[0].borderColor = v('--x-accent');
    sbChart.data.datasets[0].backgroundColor = areaFill();
    sbChart.options.scales.x.ticks.color = v('--md-default-fg-color--light');
    sbChart.options.scales.y.ticks.color = v('--md-default-fg-color--light');
    sbChart.options.scales.y.grid.color = v('--x-border');
    sbChart.update('none');
  }).observe(document.body, { attributes: true, attributeFilter: ['data-md-color-scheme'] });

  let simTimer = null;
  let simTemp = 4.2;
  let simStep = 0;

  function pushPoint(d) {
    const temp = Number(d.temp ?? 0);
    const humid = Number(d.humid ?? 0);
    const press = Number(d.pressure ?? 1013.25);
    const vib = Number(d.vib_g ?? 0);
    document.getElementById('sb-temp').innerText = `${temp.toFixed(2)} °C`;
    document.getElementById('sb-humid').innerText = `${humid.toFixed(1)} %`;
    document.getElementById('sb-press').innerText = `${press.toFixed(1)} hPa`;
    document.getElementById('sb-vib').innerText = `${vib.toFixed(3)} g${d.shock ? ' ⚡' : ''}`;
    document.getElementById('sb-raw').innerText = `[${new Date().toLocaleTimeString()}] ${JSON.stringify(d)}`;

    sbChart.data.labels.push(new Date().toLocaleTimeString());
    sbChart.data.datasets[0].data.push(temp);
    if (sbChart.data.labels.length > 25) {
      sbChart.data.labels.shift();
      sbChart.data.datasets[0].data.shift();
    }
    sbChart.update('none');
  }

  let client = null;
  const setConn = (txt, color) => {
    const el = document.getElementById('sb-conn');
    if (el) { el.innerText = txt; if (color) el.style.color = color; }
  };
  try {
    client = mqtt.connect('wss://broker.emqx.io:8084/mqtt', { clientId: 'ghp-sandbox-' + Math.random().toString(16).slice(2, 8), connectTimeout: 8000 });
    client.on('connect', () => {
      setConn('🟢 เชื่อมต่อ WSS สำเร็จ! (รับข้อมูลสดจากบอร์ด Cucumber)', 'var(--x-ok)');
      client.subscribe('tse/cn466/chanapa/telemetry');
      client.subscribe('tse/cn466/chanapa');
    });
    client.on('error', () => setConn('⚠️ เชื่อมต่อ WSS ไม่สำเร็จ — กดปุ่มโหมดจำลองแทนได้', '#f59e0b'));
    client.on('offline', () => setConn('🟠 ขาดการเชื่อมต่อ WSS ชั่วคราว (กำลังลองใหม่...)', '#f59e0b'));
    client.on('message', (topic, message) => {
      if (simTimer) return;
      try {
        const data = JSON.parse(message.toString());
        if (data.temp !== undefined) pushPoint(data);
      } catch (e) {}
    });
  } catch (e) {
    setConn('⚠️ ไม่สามารถต่อ WSS ได้ (กดปุ่มโหมดจำลองแทนได้)', '#f59e0b');
  }

  window.sbSendLed = function(mode) {
    haptic('medium');
    if (client && client.connected) {
      client.publish('tse/cn466/chanapa/cmd', JSON.stringify({ cmd: 'set_led', mode }));
      document.getElementById('sb-raw').innerText = `[TX CMD -> tse/cn466/chanapa/cmd] {"cmd":"set_led","mode":"${mode}"}`;
    } else {
      document.getElementById('sb-raw').innerText = `[OFFLINE] ยังไม่ได้เชื่อมต่อ MQTT Broker (ไม่สามารถส่งคำสั่ง LED '${mode}' ไปบอร์ดได้)`;
    }
  };

  function emitSim() {
    simStep++;
    simTemp += (Math.random() * 0.45);
    if (simTemp > 11.0) simTemp = 4.0;
    const isShock = (simStep % 5 === 0);
    pushPoint({
      node_id: 'ghp-virtual',
      temp: +simTemp.toFixed(2),
      humid: +(60 + Math.random()*8).toFixed(1),
      pressure: +(1012 + Math.random()).toFixed(1),
      vib_g: isShock ? +(0.65 + Math.random()*0.4).toFixed(3) : +(Math.random()*0.06).toFixed(3),
      shock: isShock
    });
  }

  window.sbToggleSim = function() {
    haptic('light');
    const btn = document.getElementById('sb-sim-btn');
    if (simTimer) {
      clearInterval(simTimer); simTimer = null;
      btn.innerText = '▶️ เริ่มโหมดจำลอง (Offline Demo)';
      return;
    }
    btn.innerText = '⏹️ หยุดโหมดจำลอง';
    emitSim();
    simTimer = setInterval(emitSim, 1500);
  };
})();
</script>
