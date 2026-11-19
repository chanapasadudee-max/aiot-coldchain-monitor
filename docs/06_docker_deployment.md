# บทที่ 6: การติดตั้งและรันระบบ (Docker & Port Forwarding)

> การบรรจุระบบลงใน Docker Container และการเปิดทางเชื่อมต่อภายนอก (HTTPS) เพื่อให้ Telegram Mini App ใช้งานได้

---

## 6.1 การรันด้วย Docker & Docker Compose

ระบบได้รับการออกแบบให้รันได้ในคำสั่งเดียวผ่าน `compose.yml`:

```bash
# 1. เข้าสู่โฟลเดอร์โปรเจกต์
cd aiot-coldchain-monitor

# 2. สั่งสร้างและรัน Container ในโหมด Background
docker compose up -d --build

# 3. ตรวจสอบสถานะการทำงาน
docker compose ps
```

เปิดดูหน้าเว็บแดชบอร์ดในเครื่องได้ที่: [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 6.2 การทำ Port Forwarding (HTTPS) เพื่อเปิดใน Telegram Mini App

!!! important "ข้อกำหนดของ Telegram Mini App"
    Telegram Mini App บังคับว่า **URL ต้องเป็น HTTPS เท่านั้น** ไม่สามารถใช้ `http://localhost:5000` ได้โดยตรง

### วิธีที่ 1: ใช้ GitHub Pages Live Sandbox (Zero-Tunnel 24/7 — แนะนำที่สุด!)
หน้า **Live MQTT Sandbox** บน GitHub Pages ของโปรเจกต์นี้ (`https://chanapasadudee-max.github.io/aiot-coldchain-monitor/live_sandbox/`) มี HTTPS ฟรีตลอด 24 ชม. และฝัง Telegram WebApp SDK ไว้ในตัว สามารถตั้งเป็น URL ของ Telegram Mini App ได้ทันทีแม้ปิดคอมพิวเตอร์!

### วิธีที่ 2: ใช้ Microsoft Dev Tunnels ใน VS Code (สำหรับใช้ Local AI Copilot)
1. ในหน้าต่าง VS Code คลิกที่แถบด้านล่างชื่อ **PORTS**
2. คลิกปุ่ม **Forward a Port** แล้วพิมพ์เลขพอร์ต `5000`
3. คลิกขวาที่รายการพอร์ต แล้วเปลี่ยน **Port Visibility** เป็น **Public**
4. VS Code จะสร้าง URL ให้อัตโนมัติในรูปแบบ: `https://xxxxxx-5000.asse.devtunnels.ms`
5. ตั้งค่า Environment Variable `WEBAPP_URL` แล้วรัน `python ui/bot.py`

### วิธีที่ 3: ใช้ Cloudflare Tunnel (ฟรี ไม่ต้องสมัครสมาชิก)
```bash
cloudflared tunnel --url http://localhost:5000
```
ระบบจะให้ URL สาธารณะแบบ HTTPS เช่น `https://random-words.trycloudflare.com` นำไปตั้งเป็น `WEBAPP_URL` ได้ทันที
