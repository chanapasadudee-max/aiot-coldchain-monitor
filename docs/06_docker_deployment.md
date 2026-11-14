# บทที่ 6: การติดตั้งและรันระบบ (Docker & Port Forwarding)

> การบรรจุระบบลงใน Docker Container และการเปิดทางเชื่อมต่อภายนอก (HTTPS) เพื่อให้ Telegram Mini App ใช้งานได้

---

## 6.1 การรันด้วย Docker & Docker Compose

ระบบได้รับการออกแบบให้รันได้ในคำสั่งเดียวผ่าน `compose.yml`:

```bash
# 1. เข้าสู่โฟลเดอร์โปรเจกต์
cd D:\TSE34\CN466\Project_Final

# 2. สั่งสร้างและรัน Container ในโหมด Background
docker compose up -d --build

# 3. ตรวจสอบสถานะการทำงาน
docker compose ps
```

เปิดดูหน้าเว็บแดชบอร์ดในเครื่องได้ที่: [http://localhost:5000](http://localhost:5000)

---

## 6.2 การทำ Port Forwarding (HTTPS) เพื่อเปิดใน Telegram

> [!IMPORTANT]
> Telegram Mini App บังคับว่า **URL ต้องเป็น HTTPS เท่านั้น** ไม่สามารถใช้ `http://localhost:5000` ได้โดยตรง

### วิธีที่ 1: ใช้ Microsoft Dev Tunnels ใน VS Code (แนะนำที่สุด)
1. ในหน้าต่าง VS Code คลิกที่แถบด้านล่างชื่อ **PORTS**
2. คลิกปุ่ม **Forward a Port** แล้วพิมพ์เลขพอร์ต `5000`
3. คลิกขวาที่รายการพอร์ต แล้วเปลี่ยน **Port Visibility** เป็น **Public**
4. VS Code จะสร้าง URL ให้อัตโนมัติในรูปแบบ:
   `https://xxxxxx-5000.asse.devtunnels.ms`
5. นำ URL นี้ไปใส่ใน `WEBAPP_URL` ในไฟล์ `ui/bot.py` ได้ทันที!

### วิธีที่ 2: ใช้ Cloudflare Tunnel (ฟรี ไม่ต้องสมัครสมาชิก)
หากต้องการรันผ่าน Command Line สามารถดาวน์โหลด `cloudflared` แล้วพิมพ์:
```bash
cloudflared tunnel --url http://localhost:5000
```
ระบบจะให้ URL สาธารณะแบบ HTTPS เช่น `https://random-words.trycloudflare.com` นำไปใช้งานได้ทันที
