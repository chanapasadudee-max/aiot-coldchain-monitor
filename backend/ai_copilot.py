"""
AI Copilot (Gemini 2.5 Flash Cloud + Local Ollama Fallback) + Deterministic Safety Guardrails
File: backend/ai_copilot.py
Author: Chanapa Sadudee

สถาปัตยกรรม AI + Guardrails:
  1. โหลด GEMINI_API_KEY จาก environment หรือ backend/.env (ติด .gitignore ปลอดภัย 100%)
  2. ใช้ Gemini 2.5 Flash (google-genai SDK) เป็นหลัก -> ตอบภาษาไทยเป็นธรรมชาติ ฉลาด มีบริบทการสนทนา
     และส่งคืน Structured JSON Action
  3. Safety Guardrail Engine (Deterministic Rules) ตรวจสอบทุกคำสั่งก่อนส่งไปบอร์ด Cucumber RIS:
     - ห้ามปิดไฟเตือน LED ขณะสถานะ CRITICAL (เว้นแต่ผู้ใช้ระบุ 'บังคับปิดไฟ' / force)
     - บันทึก Audit Log ทุกคำสั่ง
  4. Fallback อัตโนมัติไปยัง Local Ollama (qwen2.5) หรือ Local Intent Parser หากไม่มีเน็ต
"""

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
import requests

# Auto-load backend/.env if present (gitignored)
_ENV_FILE = Path(__file__).parent / ".env"
if _ENV_FILE.exists():
    for _line in _ENV_FILE.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip().strip('"').strip("'"))

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434/api/chat")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")

try:
    from google import genai
    from google.genai import types as genai_types
    _genai_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
except Exception:
    _genai_client = None

SYSTEM_PROMPT = """คุณคือ "AIoT Plant Engineer Copilot" ผู้ช่วยวิศวกรอัจฉริยะที่เชื่อมต่อกับบอร์ด Cucumber RIS (ESP32-S2) จริงแบบสองทาง
หน้าที่ของคุณคือสนทนาภาษาไทยอย่างเป็นธรรมชาติ ฉลาด เข้าใจบริบทวิศวกรรม Cold Chain / Server Room / IoT / GMP และแปลความต้องการของผู้ใช้เป็น Structured JSON Action

เครื่องมือ (action) ที่เลือกใช้ได้:
1. "chat" — ตอบคำถาม ให้คำแนะนำ อธิบายความรู้ หรือวิเคราะห์สถานการณ์อย่างละเอียดจากข้อมูลเซ็นเซอร์สด
2. "get_status" — สรุปสถานะอุณหภูมิ ความชื้น ความดัน แรงสั่น ความชัน และความเสี่ยงล่าสุดให้ชัดเจน
3. "get_capa_report" — สร้างรายงานวิเคราะห์สาเหตุ (Root Cause) และมาตรการแก้ไขเร่งด่วน (CAPA)
4. "set_led" — สั่งเปลี่ยนสีไฟ NeoPixel RGB LED บนบอร์ด Cucumber RIS จริง
   params: {"mode": "safe"|"warning"|"critical"|"off", "force": false|true}
   (ตั้ง force=true เฉพาะเมื่อผู้ใช้สั่งชัดเจนว่า "บังคับปิด" / "force" / "override" เท่านั้น)
5. "switch_profile" — เปลี่ยนโหมดมาตรฐานการตรวจวัด
   params: {"profile": "coldchain"|"server"|"room"}
6. "simulate_crisis" — จำลองสถานการณ์ทดสอบ
   params: {"scenario": "normal"|"warning"|"failure"|"door_slam"|"glitch"}

ข้อกำหนดสำคัญ:
- ตอบเป็น JSON object เท่านั้น โครงสร้าง:
  {"action": "...", "params": {...}, "reply": "คำตอบภาษาไทยที่เป็นธรรมชาติ อ่านง่าย มีสาระ และอ้างอิงตัวเลขเซ็นเซอร์จริงเมื่อเกี่ยวข้อง"}
"""


class SafetyGuardrails:
    """Deterministic Safety Layer: ตรวจสอบทุกคำสั่งก่อนถึงฮาร์ดแวร์จริง"""

    def validate(self, action: str, params: dict, ai_state: dict) -> tuple[bool, str]:
        risk = ai_state.get("risk_level", "NORMAL")

        if action == "set_led":
            mode = str(params.get("mode", "")).lower()
            force = bool(params.get("force", False))
            if mode not in ("safe", "warning", "critical", "off"):
                return False, f"BLOCKED: โหมดไฟ '{mode}' ไม่อยู่ในรายการที่อนุญาต (safe/warning/critical/off)"
            if mode == "off" and risk == "CRITICAL" and not force:
                return (
                    False,
                    "BLOCKED BY SAFETY GUARDRAIL: ห้ามปิดไฟแจ้งเตือนบนบอร์ด Cucumber ขณะระบบอยู่ในสถานะ CRITICAL! "
                    "(หากต้องการปิดจริง ให้พิมพ์ระบุ 'บังคับปิดไฟ')",
                )
            return True, f"ALLOWED: ผ่านกฎความปลอดภัย สั่งเปลี่ยนไฟ RGB LED -> {mode}"

        if action == "switch_profile":
            profile = str(params.get("profile", "")).lower()
            if profile not in ("coldchain", "server", "room"):
                return False, f"BLOCKED: ไม่รู้จักโหมด '{profile}' (รองรับเฉพาะ coldchain, server, room)"
            return True, f"ALLOWED: อนุญาตให้สลับมาตรฐานเป็น '{profile}'"

        if action == "simulate_crisis":
            scenario = str(params.get("scenario", "normal")).lower()
            if scenario not in ("normal", "warning", "failure", "door_slam", "glitch"):
                return False, f"BLOCKED: ไม่รู้จักสถานการณ์จำลอง '{scenario}'"
            return True, f"ALLOWED: อนุญาตให้จำลองสถานการณ์ '{scenario}'"

        return True, "ALLOWED: คำสั่งอ่านข้อมูล/สนทนาทั่วไป"


class AICopilot:
    def __init__(self):
        self.guardrails = SafetyGuardrails()
        self.audit_log: list[dict] = []
        self.chat_history: list[dict] = []

    def _build_context(self, ai_state: dict) -> str:
        return (
            f"ข้อมูลสดจากบอร์ด Cucumber RIS ตอนนี้:\n"
            f"- Profile: {ai_state.get('profile_name')} ({ai_state.get('profile')})\n"
            f"- เกณฑ์ปลอดภัย: {ai_state.get('safe_range')} °C\n"
            f"- อุณหภูมิ (HTS221): {ai_state.get('current_temp')} °C | ความชื้น: {ai_state.get('current_humid')}%\n"
            f"- ความดัน (BMP280): {ai_state.get('current_pressure')} hPa\n"
            f"- แรงสั่น (MPU6050): {ai_state.get('current_vib_g')} g (Shock={ai_state.get('shock_detected')})\n"
            f"- ความชันอุณหภูมิ (Slope): {ai_state.get('slope_per_step')} °C/step | Z-Score: {ai_state.get('z_score')}\n"
            f"- ระดับความเสี่ยง: {ai_state.get('risk_level')} | Health Score: {ai_state.get('health_score')}/100 | ETTF: {ai_state.get('ettf_seconds')}s\n"
            f"- เหตุผลความผิดปกติ: {ai_state.get('anomaly_reasons')}"
        )

    def _call_gemini(self, user_message: str, ai_state: dict) -> dict | None:
        if not _genai_client:
            return None
        try:
            history_txt = ""
            for h in self.chat_history[-6:]:
                history_txt += f"User: {h['u']}\nAssistant: {h['a']}\n"

            prompt = (
                f"[{self._build_context(ai_state)}]\n"
                + (f"\nประวัติการสนทนาล่าสุด:\n{history_txt}\n" if history_txt else "")
                + f"คำสั่ง/คำถามผู้ใช้ล่าสุด: {user_message}"
            )
            resp = _genai_client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    temperature=0.35,
                ),
            )
            raw = (resp.text or "").strip()
            match = re.search(r"\{.*\}", raw, re.S)
            if match:
                parsed = json.loads(match.group(0))
                parsed["_engine"] = f"Gemini ({GEMINI_MODEL})"
                return parsed
        except Exception as e:
            print(f"[Gemini Copilot Warning] {e}")
        return None

    def _call_ollama(self, user_message: str, ai_state: dict) -> dict | None:
        payload = {
            "model": OLLAMA_MODEL,
            "stream": False,
            "format": "json",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"[{self._build_context(ai_state)}]\nคำสั่งผู้ใช้: {user_message}"},
            ],
            "options": {"temperature": 0.2, "num_predict": 220},
        }
        try:
            resp = requests.post(OLLAMA_URL, json=payload, timeout=(0.6, 10))
            if resp.status_code == 200:
                content = resp.json().get("message", {}).get("content", "")
                match = re.search(r"\{.*\}", content, re.S)
                if match:
                    parsed = json.loads(match.group(0))
                    parsed["_engine"] = f"Ollama ({OLLAMA_MODEL})"
                    return parsed
        except Exception:
            pass
        return None

    def _fallback_parse(self, text: str, ai_state: dict) -> dict:
        t = text.lower().strip()
        force = any(k in t for k in ["บังคับ", "force", "override"])

        if any(k in t for k in ["ไฟ", "led", "rgb"]):
            if any(k in t for k in ["ปิด", "off", "ดับ"]):
                return {"action": "set_led", "params": {"mode": "off", "force": force}, "reply": "ดำเนินการส่งคำสั่งปิดไฟ RGB LED บนบอร์ด Cucumber ครับ", "_engine": "Local Intent Fallback"}
            if any(k in t for k in ["แดง", "ฉุกเฉิน", "วิกฤต", "critical", "red"]):
                return {"action": "set_led", "params": {"mode": "critical", "force": force}, "reply": "สั่งเปลี่ยนไฟ RGB LED บนบอร์ด Cucumber เป็นสีแดงกระพริบ (CRITICAL) แล้วครับ", "_engine": "Local Intent Fallback"}
            if any(k in t for k in ["เหลือง", "ส้ม", "เตือน", "warn", "gold", "yellow"]):
                return {"action": "set_led", "params": {"mode": "warning", "force": force}, "reply": "สั่งเปลี่ยนไฟ RGB LED บนบอร์ด Cucumber เป็นสีเหลืองเตือน (WARNING) แล้วครับ", "_engine": "Local Intent Fallback"}
            if any(k in t for k in ["เขียว", "ปกติ", "safe", "green", "เปิด"]):
                return {"action": "set_led", "params": {"mode": "safe", "force": force}, "reply": "สั่งเปลี่ยนไฟ RGB LED บนบอร์ด Cucumber เป็นสีเขียว (SAFE) แล้วครับ", "_engine": "Local Intent Fallback"}

        if any(k in t for k in ["โหมด", "profile", "เปลี่ยนเป็น", "สลับ"]):
            if any(k in t for k in ["server", "เซิร์ฟเวอร์", "ดาต้า"]):
                return {"action": "switch_profile", "params": {"profile": "server"}, "reply": "สลับมาตรฐานการตรวจวัดเป็นโหมด Server Room (18–24°C) เรียบร้อยครับ", "_engine": "Local Intent Fallback"}
            if any(k in t for k in ["room", "ห้องจริง", "เดโม", "บอร์ดสด", "lab"]):
                return {"action": "switch_profile", "params": {"profile": "room"}, "reply": "สลับเป็นโหมด Live Lab / ห้องจริง (20–36.5°C) เรียบร้อยครับ", "_engine": "Local Intent Fallback"}
            if any(k in t for k in ["cold", "ตู้แช่", "ยา", "วัคซีน"]):
                return {"action": "switch_profile", "params": {"profile": "coldchain"}, "reply": "สลับเป็นโหมด Cold Chain ตู้แช่ยา/วัคซีน (2–8°C) เรียบร้อยครับ", "_engine": "Local Intent Fallback"}

        if any(k in t for k in ["จำลอง", "simulate", "ทดสอบวิกฤต"]):
            if any(k in t for k in ["ดับ", "พัง", "failure", "คอม"]):
                return {"action": "simulate_crisis", "params": {"scenario": "failure"}, "reply": "จำลองเหตุการณ์คอมเพรสเซอร์ดับแล้วครับ", "_engine": "Local Intent Fallback"}
            if any(k in t for k in ["แผ่ว", "เตือน", "warning", "warn"]):
                return {"action": "simulate_crisis", "params": {"scenario": "warning"}, "reply": "จำลองเหตุการณ์แอร์เริ่มแผ่วแล้วครับ", "_engine": "Local Intent Fallback"}
            if any(k in t for k in ["กระแทก", "เขย่า", "slam", "shock"]):
                return {"action": "simulate_crisis", "params": {"scenario": "door_slam"}, "reply": "จำลองเหตุการณ์แรงกระแทกแล้วครับ", "_engine": "Local Intent Fallback"}
            if any(k in t for k in ["รบกวน", "glitch", "สไปก์", "spike"]):
                return {"action": "simulate_crisis", "params": {"scenario": "glitch"}, "reply": "จำลองเหตุการณ์สัญญาณรบกวนแล้วครับ", "_engine": "Local Intent Fallback"}
            return {"action": "simulate_crisis", "params": {"scenario": "normal"}, "reply": "จำลองสภาวะปกติแล้วครับ", "_engine": "Local Intent Fallback"}

        if any(k in t for k in ["capa", "รายงาน", "สาเหตุ", "วิธีแก้", "report"]):
            return {"action": "get_capa_report", "params": {}, "reply": "สรุปรายงาน CAPA ให้แล้วครับ", "_engine": "Local Intent Fallback"}

        return {
            "action": "get_status",
            "params": {},
            "reply": (
                f"สถานะล่าสุด ({ai_state.get('profile_name')}): "
                f"อุณหภูมิ {ai_state.get('current_temp')}°C, ความชื้น {ai_state.get('current_humid')}%, "
                f"ความดัน {ai_state.get('current_pressure')} hPa, แรงสั่น {ai_state.get('current_vib_g')}g | "
                f"ความเสี่ยง: {ai_state.get('risk_level')} (Health {ai_state.get('health_score')}/100)"
            ),
            "_engine": "Local Intent Fallback",
        }

    def process(self, user_message: str, ai_state: dict, executors: dict) -> dict:
        # 1. Gemini Cloud -> 2. Local Ollama -> 3. Local Fallback
        intent = self._call_gemini(user_message, ai_state)
        if not intent:
            intent = self._call_ollama(user_message, ai_state)
        if not intent:
            intent = self._fallback_parse(user_message, ai_state)

        action = str(intent.get("action", "get_status"))
        params = intent.get("params")
        if not isinstance(params, dict):
            params = {}
        reply = str(intent.get("reply", ""))
        engine_used = intent.get("_engine", "Local Engine")

        allowed, guardrail_msg = self.guardrails.validate(action, params, ai_state)

        exec_result = None
        if allowed:
            fn = executors.get(action)
            if fn:
                exec_result = fn(params)
                if action == "get_capa_report" and isinstance(exec_result, dict) and not reply:
                    reply = exec_result.get("summary_text", reply)
        else:
            reply = f"🛡️ {guardrail_msg}"

        self.chat_history.append({"u": user_message, "a": reply})
        self.chat_history = self.chat_history[-10:]

        audit_entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "user_message": user_message,
            "engine": engine_used,
            "action": action,
            "params": params,
            "allowed": allowed,
            "guardrail_note": guardrail_msg,
        }
        self.audit_log.insert(0, audit_entry)
        self.audit_log = self.audit_log[:50]

        return {
            "reply": reply,
            "action": action,
            "params": params,
            "engine": engine_used,
            "guardrail_allowed": allowed,
            "guardrail_note": guardrail_msg,
            "exec_result": exec_result,
        }
