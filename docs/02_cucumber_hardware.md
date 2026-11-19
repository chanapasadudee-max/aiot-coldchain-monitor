# บทที่ 2: บอร์ด Cucumber RIS & Multi-Sensor (Hardware & PlatformIO)

> คู่มือการพัฒนาเฟิร์มแวร์ภาษา C++ (PlatformIO / ESP32-S2) อ่านเซ็นเซอร์ I2C พร้อมกัน 3 ชนิด และควบคุมไฟ NeoPixel RGB LED แบบสองทางผ่าน MQTT

---

## 2.1 อุปกรณ์บนบอร์ด Cucumber RIS (ESP32-S2) ที่ใช้งานจริง

บอร์ด **Gravitech Cucumber RIS** มีเซ็นเซอร์ระดับอุตสาหกรรมและแอคชูเอเตอร์ติดตั้งมาให้บนบอร์ดครบชุด (เชื่อมผ่านบัส **I2C: SDA=41, SCL=40**):

| ชิป / อุปกรณ์ | I2C Address / Pin | หน้าที่ในระบบ Cold Chain & Server Room |
|:---|:---:|---|
| **HTS221** | `0x5F` | วัดอุณหภูมิ (°C) และความชื้นสัมพัทธ์ (%RH) ความแม่นยำสูง |
| **BMP280** | `0x76` | วัดความดันบรรยากาศ (hPa) ช่วยตรวจจับการเปิดประตูห้องเย็น/แรงดันตก |
| **MPU6050** | `0x68` | วัดความเร่ง 6 แกน คำนวณแรงสั่นสะเทือน (G-force) จับแรงกระแทก/คอมเพรสเซอร์สั่น |
| **NeoPixel RGB LED** | `GPIO 18` | แอคชูเอเตอร์แสดงสถานะไฟจริง (🟢 Safe / 🟡 Warning / 🔴 Critical Blink) รับคำสั่งจาก AI |

---

## 2.2 โครงสร้างโปรเจกต์ PlatformIO (`devices/cucumber_pio/`)

```text
devices/cucumber_pio/
├── platformio.ini            # บอร์ด esp32-s2-saola-1 + ไลบรารี HTS221, BMP280, MPU6050, NeoPixel
├── include/
│   ├── secrets.example.h     # แม่แบบการตั้งค่า Wi-Fi / MQTT (อัปโหลดขึ้น GitHub)
│   └── secrets.h             # รหัส Wi-Fi จริง (ติด .gitignore ไม่หลุดขึ้น GitHub)
└── src/
    └── main.cpp              # I2C Auto-Scan + High-rate Vibration Sampling + Bidirectional MQTT
```

### คำสั่ง Build และ Flash ลงบอร์ดจริง
```bash
cd devices/cucumber_pio
pio run -t upload --upload-port COM6
```

### ตัวอย่างผลลัพธ์จริงจาก Serial Monitor บนบอร์ด Cucumber RIS (`COM6`)
```text
====================================================
  AIoT Cold Chain Monitor — Cucumber RIS (ESP32-S2)
====================================================
[I2C] Scanning bus (SDA=41, SCL=40)...
  -> Found I2C device at 0x5F
  -> Found I2C device at 0x68
  -> Found I2C device at 0x76
[I2C] Scan complete. Total devices: 3
[SENSOR] HTS221 ready (Temp/Humid)
[SENSOR] BMP280 ready (Pressure)
[SENSOR] MPU6050 ready (Vibration/Shock)
[WiFi] Connected!
[MQTT] Subscribed CMD: tse/cn466/chanapa/cmd
[TELEMETRY] {"node_id":"cucumber-ris-01","temp":34.50,"humid":49.20,"pressure":1008.40,"vib_g":0.025,"shock":false,"led_mode":"safe","sensors":["HTS221","BMP280","MPU6050"]}
```

---

## 2.3 กรณีไม่มีบอร์ดจริง? ใช้ Industrial Multi-Sensor Simulator

```bash
# โหมดปกติ (ตู้แช่ยา 2–6°C)
python devices/simulator/sim_industrial.py --scenario normal

# โหมดวิกฤตคอมเพรสเซอร์ดับ
python devices/simulator/sim_industrial.py --scenario failure

# โหมดตรวจจับแรงกระแทก/เปิดประตูแรง (MPU6050 Shock)
python devices/simulator/sim_industrial.py --scenario door_slam
```
