"""
Telegram Bot & Mini App + AI Copilot Integration (@Chanaps_Bot)
File: ui/bot.py
Author: Chanapa Sadudee (6610680214)

ความสามารถ:
  1. ปุ่ม Menu Button & Inline Button เปิด Telegram Mini App (GitHub Pages Live Sandbox 24/7 หรือ DevTunnel)
  2. พิมพ์แชตภาษาไทยคุยกับ AI Copilot (Ollama + Guardrails) เพื่อสั่งคุมบอร์ด Cucumber จริง
  3. คำสั่งด่วน: /start, /status, /report, /led <safe|warning|critical|off>, /profile <coldchain|server|room>
  4. Background Alert Watcher: แจ้งเตือนอัตโนมัติเมื่อระบบเข้าขั้น WARNING หรือ CRITICAL (HTML Safe Escaping)

วิธีรัน:
  set TELEGRAM_BOT_TOKEN=<YOUR_BOT_TOKEN>
  python ui/bot.py
"""

import asyncio
import html
import logging
import os
import sys
import time
import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, MenuButtonWebApp, Update, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://127.0.0.1:5000")
# ใช้หน้า Live MQTT Sandbox บน GitHub Pages เป็นค่าเริ่มต้น (HTTPS 24/7 ไม่ต้องเปิด Tunnel)
WEBAPP_URL = os.getenv(
    "WEBAPP_URL",
    "https://chanapasadudee-max.github.io/aiot-coldchain-monitor/live_sandbox/",
)

registered_chats: set[int] = set()
last_alert_time: float = 0.0
ALERT_COOLDOWN_SEC = 60.0


def esc(val) -> str:
    return html.escape(str(val))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    registered_chats.add(chat_id)

    if WEBAPP_URL.startswith("https://"):
        try:
            await context.bot.set_chat_menu_button(
                chat_id=chat_id,
                menu_button=MenuButtonWebApp(text="📊 เปิด Mini App", web_app=WebAppInfo(url=WEBAPP_URL)),
            )
        except Exception as e:
            logging.warning(f"Menu button warning: {e}")

    buttons = []
    if WEBAPP_URL.startswith("https://"):
        buttons.append([InlineKeyboardButton("❄️ เปิด Industrial Mini App", web_app=WebAppInfo(url=WEBAPP_URL))])

    welcome_text = (
        "🏭 <b>AIoT Industrial Cold Chain Copilot</b>\n"
        "เชื่อมต่อบอร์ด Cucumber RIS (HTS221 + BMP280 + MPU6050 + RGB LED) เรียบร้อยแล้ว!\n\n"
        "💬 <b>พิมพ์แชตภาษาไทยได้เลย</b> เช่น:\n"
        "• \"สรุปสถานะตอนนี้\"\n"
        "• \"เปิดไฟสีแดงฉุกเฉิน\"\n"
        "• \"เปลี่ยนเป็นโหมดห้องเซิร์ฟเวอร์\"\n\n"
        "⚡ <b>คำสั่งด่วน:</b>\n"
        "<code>/status</code> | <code>/report</code> | <code>/led safe|warning|critical|off</code> | <code>/profile coldchain|server|room</code>"
    )
    markup = InlineKeyboardMarkup(buttons) if buttons else None
    await update.message.reply_text(welcome_text, reply_markup=markup, parse_mode="HTML")


async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    registered_chats.add(update.effective_chat.id)
    try:
        resp = await asyncio.to_thread(requests.get, f"{BACKEND_API_URL}/api/latest", timeout=4)
        res = resp.json()
        ai = res.get("ai_evaluation", {})
        risk = ai.get("risk_level", "NORMAL")
        icon = "🟢" if risk == "NORMAL" else ("🟡" if risk == "WARNING" else "🚨")
        msg = (
            f"{icon} <b>สถานะล่าสุด ({esc(ai.get('profile_name'))})</b>\n"
            f"🌡️ อุณหภูมิ: <code>{esc(ai.get('current_temp'))}°C</code> (เกณฑ์ <code>{esc(ai.get('safe_range'))}</code>)\n"
            f"💧 ความชื้น: <code>{esc(ai.get('current_humid'))}%</code> | 🧭 ความดัน: <code>{esc(ai.get('current_pressure'))} hPa</code>\n"
            f"📳 แรงสั่น: <code>{esc(ai.get('current_vib_g'))}g</code> | ❤️ Health: <code>{esc(ai.get('health_score'))}/100</code>\n"
            f"🛡️ ความเสี่ยง AI: <b>{esc(risk)}</b>"
        )
    except Exception as e:
        msg = f"❌ ติดต่อ Backend ไม่ได้: <code>{esc(e)}</code>"
    await update.message.reply_text(msg, parse_mode="HTML")


async def report_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    registered_chats.add(update.effective_chat.id)
    try:
        resp = await asyncio.to_thread(requests.get, f"{BACKEND_API_URL}/api/incident-report", timeout=4)
        rep = resp.json()
        msg = esc(rep.get("summary_text", "ไม่มีรายงาน"))
    except Exception as e:
        msg = f"❌ ดึงรายงาน CAPA ไม่สำเร็จ: <code>{esc(e)}</code>"
    await update.message.reply_text(msg, parse_mode="HTML")


async def led_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = context.args[0].lower() if context.args else "safe"
    try:
        res = await asyncio.to_thread(
            requests.post, f"{BACKEND_API_URL}/api/command/led", json={"mode": mode}, timeout=4
        )
        if res.status_code == 200:
            msg = f"💡 สั่งเปลี่ยนไฟ RGB LED บนบอร์ด Cucumber → <code>{esc(mode.upper())}</code> แล้วครับ"
        else:
            msg = f"🛡️ {esc(res.json().get('detail', 'คำสั่งถูกบล็อก'))}"
    except Exception as e:
        msg = f"❌ ส่งคำสั่งไม่สำเร็จ: <code>{esc(e)}</code>"
    await update.message.reply_text(msg, parse_mode="HTML")


async def profile_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    profile = context.args[0].lower() if context.args else "coldchain"
    try:
        res = await asyncio.to_thread(
            requests.post, f"{BACKEND_API_URL}/api/profile", json={"profile": profile}, timeout=4
        )
        if res.status_code == 200:
            info = res.json()["profile"]
            msg = f"✅ สลับโหมดเป็น <b>{esc(info['name'])}</b> (เกณฑ์ {esc(info['safe_range'][0])}–{esc(info['safe_range'][1])}°C)"
        else:
            msg = f"❌ {esc(res.json().get('detail'))}"
    except Exception as e:
        msg = f"❌ สลับโหมดไม่สำเร็จ: <code>{esc(e)}</code>"
    await update.message.reply_text(msg, parse_mode="HTML")


async def chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    registered_chats.add(update.effective_chat.id)
    text = update.message.text
    try:
        resp = await asyncio.to_thread(
            requests.post, f"{BACKEND_API_URL}/api/chat", json={"message": text}, timeout=15
        )
        res = resp.json()
        badge = "✅ Guardrail OK" if res.get("guardrail_allowed") else "🛡️ Guardrail Blocked"
        reply = (
            f"{esc(res.get('reply'))}\n\n"
            f"<i>[{esc(res.get('engine'))} • {esc(res.get('action'))} • {badge}]</i>"
        )
    except Exception as e:
        reply = f"❌ ไม่สามารถติดต่อ AI Copilot ได้: <code>{esc(e)}</code>"
    await update.message.reply_text(reply, parse_mode="HTML")


async def alert_watcher(context: ContextTypes.DEFAULT_TYPE):
    global last_alert_time
    if not registered_chats or (time.time() - last_alert_time < ALERT_COOLDOWN_SEC):
        return
    try:
        resp = await asyncio.to_thread(requests.get, f"{BACKEND_API_URL}/api/latest", timeout=3)
        ai = resp.json().get("ai_evaluation", {})
        if ai.get("risk_level") in ("WARNING", "CRITICAL"):
            rep_resp = await asyncio.to_thread(requests.get, f"{BACKEND_API_URL}/api/incident-report", timeout=3)
            text = esc(rep_resp.json().get("summary_text", "⚠️ ตรวจพบความผิดปกติ!"))
            for cid in list(registered_chats):
                try:
                    await context.bot.send_message(chat_id=cid, text=text, parse_mode="HTML")
                except Exception as send_err:
                    logging.warning(f"Alert send failed for chat {cid}: {send_err}")
            last_alert_time = time.time()
    except Exception as e:
        logging.warning(f"Alert watcher poll error: {e}")


def main():
    if not BOT_TOKEN:
        print("❌ กรุณาตั้งค่า environment variable TELEGRAM_BOT_TOKEN ก่อนรันบอท!")
        print("   ตัวอย่าง (PowerShell): $env:TELEGRAM_BOT_TOKEN='YOUR_TOKEN'; py ui/bot.py")
        sys.exit(1)

    print("=" * 64)
    print(" Telegram AIoT Copilot Bot (@Chanaps_Bot)")
    print(f" Backend: {BACKEND_API_URL}")
    print(f" Mini App: {WEBAPP_URL}")
    print("=" * 64)
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("report", report_cmd))
    app.add_handler(CommandHandler("led", led_cmd))
    app.add_handler(CommandHandler("profile", profile_cmd))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), chat_handler))

    if app.job_queue:
        app.job_queue.run_repeating(alert_watcher, interval=10, first=5)

    app.run_polling()


if __name__ == "__main__":
    main()
