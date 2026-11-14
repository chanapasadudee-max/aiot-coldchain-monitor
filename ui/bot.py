"""
Telegram Bot & Mini App Integration for Industrial Cold Chain
File: bot.py
Author: Chanapa Sadudee (6610680214)

แชตบอต Telegram สำหรับ:
  1. ส่งปุ่ม WebApp เพื่อเปิด Telegram Mini App (Dashboard)
  2. รายงานสถานะอุณหภูมิและความชื้นแบบ Real-Time ด้วยคำสั่ง /status
  3. สรุปรายงานวิเคราะห์สาเหตุ (Root Cause Analysis) ด้วยคำสั่ง /report
  4. มอนิเตอร์และส่งข้อความเตือนภัยฉุกเฉินอัตโนมัติ (Automated Crisis Alert)
"""

import asyncio
import logging
import os
import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, MenuButtonWebApp, Update, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ---------------- การตั้งค่า ----------------
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8659693742:AAET9v5UZjv8CaoEPJEznf_vz-bEknQS6r0")
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://127.0.0.1:5000")
# URL ของ Mini App (หากทำ Dev Tunnels หรือ Cloudflare ให้เปลี่ยน URL ตรงนี้)
WEBAPP_URL = os.getenv("WEBAPP_URL", "http://127.0.0.1:5000")

# เก็บ Chat ID ล่าสุดเพื่อยิงแจ้งเตือน
registered_chats = set()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    registered_chats.add(chat_id)

    # ตั้งค่า Menu Button ด้านล่างแชต
    try:
        await context.bot.set_chat_menu_button(
            chat_id=chat_id,
            menu_button=MenuButtonWebApp(text="📊 เปิด Mini App", web_app=WebAppInfo(url=WEBAPP_URL))
        )
    except Exception as e:
        logging.warning(f"Set menu button warning: {e}")

    keyboard = [
        [InlineKeyboardButton("❄️ เปิด Industrial Mini App", web_app=WebAppInfo(url=WEBAPP_URL))],
        [
            InlineKeyboardButton("📊 เช็กสถานะล่าสุด", callback_data="status"),
            InlineKeyboardButton("🛠️ วิเคราะห์ปัญหา (CAPA)", callback_data="report")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = (
        "🏭 **ระบบเฝ้าระวังตู้แช่ยา & ห้อง Server อุตสาหกรรม (AIoT)**\n"
        "สวัสดีครับ! บอทนี้เชื่อมต่อกับบอร์ด Cucumber และระบบ AI Anomaly Detection\n\n"
        "💡 **คำสั่งที่ใช้งานได้:**\n"
        "• `/status` - ตรวจสอบอุณหภูมิและความเสี่ยงปัจจุบัน\n"
        "• `/report` - ขอรายงานวิเคราะห์สาเหตุและมาตรการแก้ไข (AI CAPA)\n\n"
        "👇 กดปุ่มด้านล่างเพื่อเปิด **Telegram Mini App Dashboard**:"
    )
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        res = requests.get(f"{BACKEND_API_URL}/api/latest", timeout=3)
        if res.status_code == 200:
            data = res.json()
            ai = data.get("ai_evaluation", {})
            temp = ai.get("current_temp", "N/A")
            humid = ai.get("current_humid", "N/A")
            risk = ai.get("risk_level", "NORMAL")
            slope = ai.get("slope_per_step", 0.0)

            icon = "🟢" if risk == "NORMAL" else ("🟡" if risk == "WARNING" else "🚨")
            msg = (
                f"{icon} **สถานะปัจจุบันของตู้แช่ยา:**\n"
                f"🌡️ อุณหภูมิ: `{temp}°C` (เกณฑ์ปลอดภัย: 2 - 8°C)\n"
                f"💧 ความชื้น: `{humid}%`\n"
                f"📈 แนวโน้มอุณหภูมิ: `{slope:+.3f}°C/step`\n"
                f"🛡️ ระดับความเสี่ยง AI: **{risk}**"
            )
        else:
            msg = "❌ ไม่สามารถดึงข้อมูลจากเซิร์ฟเวอร์ Backend ได้"
    except Exception as e:
        msg = f"❌ ไม่สามารถเชื่อมต่อกับ Backend ({BACKEND_API_URL}): {e}"

    await update.message.reply_text(msg, parse_mode="Markdown")

async def report_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        res = requests.get(f"{BACKEND_API_URL}/api/incident-report", timeout=3)
        if res.status_code == 200:
            rep = res.json()
            msg = rep.get("summary_text", "ไม่มีรายงานสรุปในขณะนี้")
        else:
            msg = "❌ ดึงรายงานไม่สำเร็จ"
    except Exception as e:
        msg = f"❌ ติดต่อเซิร์ฟเวอร์ไม่สำเร็จ: {e}"

    await update.message.reply_text(msg, parse_mode="Markdown")

def main():
    print("=" * 60)
    print(" 🤖 Telegram Bot for AIoT Cold Chain Monitor")
    print(f" Backend URL: {BACKEND_API_URL}")
    print(f" Mini App URL: {WEBAPP_URL}")
    print("=" * 60)

    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status_cmd))
    application.add_handler(CommandHandler("report", report_cmd))

    print("✅ บอทกำลัง Polling รอรับคำสั่งใน Telegram...")
    application.run_polling()

if __name__ == "__main__":
    main()
