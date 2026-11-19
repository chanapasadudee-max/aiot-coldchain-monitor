# 🧪 Live MQTT Sandbox (ทดลองเล่นสดบน GitHub Pages)

> หน้านี้เชื่อมต่อกับ **MQTT Broker สาธารณะ (`wss://broker.emqx.io:8084/mqtt`)** โดยตรงจากเบราว์เซอร์ของคุณ!  
> สามารถดูข้อมูลสดจากบอร์ด **Cucumber RIS (HTS221 + BMP280 + MPU6050)** หรือกดปุ่ม **จำลองวิกฤต (Virtual Simulator)** ได้ทันทีโดยไม่ต้องเปิดเซิร์ฟเวอร์ในเครื่อง

<div id="sandbox-root" style="margin-top: 16px;">
  <div style="display:flex; gap:10px; flex-wrap:wrap; align-items:center; margin-bottom:14px; padding:12px 16px; border-radius:14px; border:1px solid rgba(255,208,79,0.3); background:rgba(140,24,28,0.14);">
    <span id="sb-conn" style="font-weight:700; color:#ffd04f;">⏳ กำลังเชื่อมต่อ WSS broker.emqx.io:8084...</span>
    <span style="font-size:0.8rem; opacity:0.85;">Topic: <code>tse/cn466/chanapa/telemetry</code></span>
    <div style="margin-left:auto; display:flex; gap:8px; flex-wrap:wrap;">
      <button onclick="sbToggleSim()" id="sb-sim-btn" style="padding:6px 12px; border-radius:8px; border:1px solid #ffd04f; background:#8c181c; color:#fff; font-weight:700; cursor:pointer;">▶️ เริ่มโหมดจำลอง (Offline Demo)</button>
      <button onclick="sbSendLed('safe')" style="padding:6px 10px; border-radius:8px; border:1px solid #10b981; background:transparent; color:inherit; font-weight:700; cursor:pointer;">🟢 ไฟเขียว</button>
      <button onclick="sbSendLed('warning')" style="padding:6px 10px; border-radius:8px; border:1px solid #ffd04f; background:transparent; color:inherit; font-weight:700; cursor:pointer;">🟡 ไฟเหลือง</button>
      <button onclick="sbSendLed('critical')" style="padding:6px 10px; border-radius:8px; border:1px solid #ef4444; background:transparent; color:inherit; font-weight:700; cursor:pointer;">🔴 ไฟแดง</button>
    </div>
  </div>

  <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(160px, 1fr)); gap:12px; margin-bottom:16px;">
    <div style="padding:14px; border-radius:14px; border:1px solid rgba(255,255,255,0.12); background:rgba(22,25,33,0.75); color:#f8fafc;">
      <div style="font-size:0.75rem; color:#94a3b8;">🌡️ อุณหภูมิ (HTS221)</div>
      <div id="sb-temp" style="font-size:1.7rem; font-weight:800; color:#ffd04f;">-- °C</div>
    </div>
    <div style="padding:14px; border-radius:14px; border:1px solid rgba(255,255,255,0.12); background:rgba(22,25,33,0.75); color:#f8fafc;">
      <div style="font-size:0.75rem; color:#94a3b8;">💧 ความชื้น (HTS221)</div>
      <div id="sb-humid" style="font-size:1.7rem; font-weight:800; color:#38bdf8;">-- %</div>
    </div>
    <div style="padding:14px; border-radius:14px; border:1px solid rgba(255,255,255,0.12); background:rgba(22,25,33,0.75); color:#f8fafc;">
      <div style="font-size:0.75rem; color:#94a3b8;">🧭 ความดัน (BMP280)</div>
      <div id="sb-press" style="font-size:1.7rem; font-weight:800; color:#f8fafc;">-- hPa</div>
    </div>
    <div style="padding:14px; border-radius:14px; border:1px solid rgba(255,255,255,0.12); background:rgba(22,25,33,0.75); color:#f8fafc;">
      <div style="font-size:0.75rem; color:#94a3b8;">📳 แรงสั่น (MPU6050)</div>
      <div id="sb-vib" style="font-size:1.7rem; font-weight:800; color:#10b981;">-- g</div>
    </div>
  </div>

  <div style="padding:16px; border-radius:16px; border:1px solid rgba(255,255,255,0.12); background:rgba(22,25,33,0.75); height:260px;">
    <canvas id="sbChart"></canvas>
  </div>

  <pre id="sb-raw" style="margin-top:12px; padding:12px; border-radius:12px; font-size:0.75rem; max-height:140px; overflow:auto;">กำลังรอรับข้อความ JSON จากบอร์ด Cucumber...</pre>
</div>

<script src="https://unpkg.com/mqtt@5.10.1/dist/mqtt.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<script>
(function() {
  const ctx = document.getElementById('sbChart').getContext('2d');
  const sbChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: [],
      datasets: [
        { label: 'Temperature (°C)', data: [], borderColor: '#ffd04f', backgroundColor: 'rgba(255,208,79,0.18)', fill: true, tension: 0.35, borderWidth: 2.5 }
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      scales: {
        x: { ticks: { color: '#94a3b8', font: { size: 10 } } },
        y: { ticks: { color: '#94a3b8', font: { size: 10 } }, grid: { color: 'rgba(255,255,255,0.08)' } }
      },
      plugins: { legend: { labels: { color: '#f8fafc' } } }
    }
  });

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
  try {
    client = mqtt.connect('wss://broker.emqx.io:8084/mqtt', { clientId: 'ghp-sandbox-' + Math.random().toString(16).slice(2, 8) });
    client.on('connect', () => {
      document.getElementById('sb-conn').innerText = '🟢 เชื่อมต่อ WSS สำเร็จ! (รับข้อมูลสดจากบอร์ด Cucumber)';
      document.getElementById('sb-conn').style.color = '#10b981';
      client.subscribe('tse/cn466/chanapa/telemetry');
      client.subscribe('tse/cn466/chanapa');
    });
    client.on('message', (topic, message) => {
      try {
        const data = JSON.parse(message.toString());
        if (data.temp !== undefined) pushPoint(data);
      } catch (e) {}
    });
  } catch (e) {
    document.getElementById('sb-conn').innerText = '⚠️ ไม่สามารถต่อ WSS ได้ (กดปุ่มโหมดจำลองแทนได้)';
  }

  window.sbSendLed = function(mode) {
    if (client && client.connected) {
      client.publish('tse/cn466/chanapa/cmd', JSON.stringify({ cmd: 'set_led', mode }));
      document.getElementById('sb-raw').innerText = `[TX CMD -> tse/cn466/chanapa/cmd] {"cmd":"set_led","mode":"${mode}"}`;
    }
  };

  let simTimer = null;
  let simTemp = 4.2;
  window.sbToggleSim = function() {
    const btn = document.getElementById('sb-sim-btn');
    if (simTimer) {
      clearInterval(simTimer); simTimer = null;
      btn.innerText = '▶️ เริ่มโหมดจำลอง (Offline Demo)';
      return;
    }
    btn.innerText = '⏹️ หยุดโหมดจำลอง';
    simTimer = setInterval(() => {
      simTemp += (Math.random() * 0.45);
      if (simTemp > 11.0) simTemp = 4.0;
      pushPoint({ node_id: 'ghp-virtual', temp: +simTemp.toFixed(2), humid: +(60 + Math.random()*8).toFixed(1), pressure: +(1012 + Math.random()).toFixed(1), vib_g: +(Math.random()*0.08).toFixed(3), shock: false });
    }, 1500);
  };
})();
</script>
