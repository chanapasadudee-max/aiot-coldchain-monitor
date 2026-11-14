# บทที่ 5: ส่วนติดต่อผู้ใช้งาน (UI & Telegram Mini App)

> การสร้าง Dashboard สำหรับสมาร์ตโฟนด้วย HTML/CSS/JS และการผสาน Telegram Mini App SDK

---

## 5.1 ทำไมต้อง Telegram Mini App?

ในโรงงานและสถานพยาบาล วิศวกรและเภสัชกรไม่ได้นั่งเฝ้าหน้าจอคอมพิวเตอร์ตลอดเวลา การพัฒนา UI ผ่าน **Telegram Mini App (TMA)** ช่วยให้:

1. **ไม่ต้องดาวน์โหลดแอปเพิ่ม:** เปิดดูได้ทันทีผ่านแอป Telegram บน iOS, Android และ PC
2. **เปิดผ่านปุ่มเดียวในแชต:** เมื่อได้รับแจ้งเตือนฉุกเฉิน สามารถแตะปุ่มเพื่อเปิดแดชบอร์ดดูสถิติและกราฟได้ทันที
3. **ระบบสั่นตอบสนอง (Haptic Feedback):** เมื่อกดปุ่มหรือเกิดวิกฤต โทรศัพท์จะสั่นเตือนผู้ใช้งาน

---

## 5.2 การฝัง Telegram WebApp SDK ในไฟล์ HTML

ในไฟล์ `ui/static/index.html` เราเรียกใช้สคริปต์ทางการของ Telegram:

```html
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<script>
  // เริ่มต้นการทำงานของ Telegram WebApp
  const tg = window.Telegram?.WebApp;
  if (tg) {
    tg.ready();
    tg.expand(); // ขยายให้เต็มจอสมาร์ตโฟน
    
    // ตั้งค่าสีธีมให้ตรงกับแอป Telegram
    if (tg.setHeaderColor) tg.setHeaderColor('#0b1120');
  }

  // เรียกใช้ Haptic เมื่อกดปุ่ม
  function vibrateAlert() {
    tg?.HapticFeedback?.impactOccurred('heavy');
  }
</script>
```

---

## 5.3 โค้ดเชื่อมต่อ Telegram Bot (`ui/bot.py`)

เราพัฒนาบอทด้วยไลบรารี `python-telegram-bot` เพื่อทำหน้าที่ 2 ประการ:

1. **ส่งข้อความแจ้งเตือนเมื่อ AI ตรวจพบวิกฤต**
2. **สร้างปุ่มเปิด Mini App ให้ปรากฏในห้องแชตตลอดเวลา:**

```python
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, MenuButtonWebApp, WebAppInfo

async def start(update, context):
    chat_id = update.effective_chat.id
    
    # ตั้งปุ่ม Menu Button ด้านล่างซ้ายของช่องพิมพ์
    await context.bot.set_chat_menu_button(
        chat_id=chat_id,
        menu_button=MenuButtonWebApp(text="📊 เปิด Mini App", web_app=WebAppInfo(url=WEBAPP_URL))
    )
    
    # ส่งปุ่ม Inline ในแชต
    keyboard = [[InlineKeyboardButton("❄️ เปิด Industrial Mini App", web_app=WebAppInfo(url=WEBAPP_URL))]]
    await update.message.reply_text("ระบบพร้อมใช้งาน!", reply_markup=InlineKeyboardMarkup(keyboard))
```
