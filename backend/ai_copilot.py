"""
Local AI Copilot (Ollama qwen2.5) + Deterministic Safety Guardrails
File: ai_copilot.py
Author: Chanapa Sadudee (6610680214)

สถาปัตยกรรม AI + Guardrails (อ้างอิงแนวคิดความปลอดภัย AIoT):
  1. AI Copilot (Ollama qwen2.5:3b / qwen2.5:7b) ทำหน้าที่แปลข้อความภาษาไทยเป็น
     Structured JSON Intent / Tool Call
  2. Safety Guardrail Engine (กฎที่ตรวจสอบได้ 100%) ตรวจสอบทุกคำสั่งก่อนส่งไปบอร์ด Cucumber:
     - ห้ามสั่งปิดไฟเตือน LED ขณะระบบอยู่ในสถานะ CRITICAL (เว้นแต่ผู้ใช้ระบุ 'บังคับปิด' / force_override)
     - ตรวจสอบค่า Profile ที่อนุญาตเท่านั้น (coldchain, server, room)
     - บันทึก Audit Log ทุกคำสั่งทั้งที่อนุญาต (ALLOWED) และถูกบล็อก (BLOCKED)
  3. Instant Deterministic Fallback: ทำงานได้แม่นยำ 100% แม้ยังไม่ได้เปิด Ollama Server
"""

import json
import os
import re
from datetime import datetime, timezone
import requests

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434/api/chat")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")

SYSTEM_PROMPT = """คุณคือ "TSE AIoT Plant Engineer Copilot" ผู้ช่วยวิศวกรอัจฉริยะที่เชื่อมต่อกับบอร์ด Cucumber RIS (ESP32-S2)
หน้าที่ของคุณคือวิเคราะห์คำสั่งภาษาไทยหรืออังกฤษของผู้ใช้ แล้วตอบกลับเป็น JSON เท่านั้น ห้ามมีข้อความอื่นนอก JSON

เครื่องมือ (action) ที่คุณเลือกใช้ได้:
1. "get_status" — รายงานค่าอุณหภูมิ ความชื้น ความดัน แรงสั่น และความเสี่ยงล่าสุด
2. "get_capa_report" — ขอรายงานวิเคราะห์สาเหตุและมาตรการแก้ไข (CAPA)
3. "set_led" — สั่งเปลี่ยนสีไฟ NeoPixel RGB LED บนบอร์ด Cucumber จริง
   params: {"mode": "safe"|"warning"|"critical"|"off", "force": false|true}
4. "switch_profile" — เปลี่ยนโหมดมาตรฐานการตรวจวัด
   params: {"profile": "coldchain"|"server"|"room"}
5. "simulate_crisis" — จำลองสถานการณ์ทดสอบ
   params: {"scenario": "normal"|"warning"|"failure"|"door_slam"|"glitch"}
6. "chat" — ตอบคำถามความรู้เรื่อง AIoT / Cold Chain / บอร์ด Cucumber ทั่วไป

รูปแบบ JSON ที่ต้องตอบ:
{"action": "...", "params": {...}, "reply": "คำตอบภาษาไทยที่สุภาพ กระชับ และเป็นมืออาชีพ"}
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

    def _call_ollama(self, user_message: str, ai_state: dict) -> dict | None:
        context_str = (
            f"ข้อมูลสดจากบอร์ด Cucumber ตอนนี้: "
            f"Profile={ai_state.get('profile_name')}, "
            f"Temp={ai_state.get('current_temp')}°C (เกณฑ์ {ai_state.get('safe_range')}), "
            f"Humid={ai_state.get('current_humid')}%, "
            f"Pressure={ai_state.get('current_pressure')} hPa, "
            f"Vib={ai_state.get('current_vib_g')}g, "
            f"Slope={ai_state.get('slope_per_step')}, "
            f"Risk={ai_state.get('risk_level')}, "
            f"HealthScore={ai_state.get('health_score')}/100"
        )
        payload = {
            "model": OLLAMA_MODEL,
            "stream": False,
            "format": "json",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"[{context_str}]\nคำสั่งผู้ใช้: {user_message}"},
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

        # 1. LED commands
        if any(k in t for k in ["ไฟ", "led", "rgb"]):
            if any(k in t for k in ["ปิด", "off", "ดับ"]):
                return {
                    "action": "set_led",
                    "params": {"mode": "off", "force": force},
                    "reply": "ดำเนินการส่งคำสั่งปิดไฟ RGB LED บนบอร์ด Cucumber ครับ",
                    "_engine": "Local Rule/Intent Engine",
                }
            if any(k in t for k in ["แดง", "ฉุกเฉิน", "วิกฤต", "critical", "red"]):
                return {
                    "action": "set_led",
                    "params": {"mode": "critical", "force": force},
                    "reply": "สั่งเปลี่ยนไฟ RGB LED บนบอร์ด Cucumber เป็นสีแดงกระพริบ (CRITICAL) แล้วครับ",
                    "_engine": "Local Rule/Intent Engine",
                }
            if any(k in t for k in ["เหลือง", "ส้ม", "เตือน", "warn", "gold", "yellow"]):
                return {
                    "action": "set_led",
                    "params": {"mode": "warning", "force": force},
                    "reply": "สั่งเปลี่ยนไฟ RGB LED บนบอร์ด Cucumber เป็นสีทอง/เหลืองเตือน (WARNING) แล้วครับ",
                    "_engine": "Local Rule/Intent Engine",
                }
            if any(k in t for k in ["เขียว", "ปกติ", "safe", "green", "เปิด"]):
                return {
                    "action": "set_led",
                    "params": {"mode": "safe", "force": force},
                    "reply": "สั่งเปลี่ยนไฟ RGB LED บนบอร์ด Cucumber เป็นสีเขียว (SAFE) แล้วครับ",
                    "_engine": "Local Rule/Intent Engine",
                }

        # 2. Profile switch
        if any(k in t for k in ["โหมด", "profile", "เปลี่ยนเป็น", "สลับ"]):
            if any(k in t for k in ["server", "เซิร์ฟเวอร์", "ดาต้า"]):
                return {
                    "action": "switch_profile",
                    "params": {"profile": "server"},
                    "reply": "สลับมาตรฐานการตรวจวัดเป็นโหมด Server Room (18–24°C) เรียบร้อยครับ",
                    "_engine": "Local Rule/Intent Engine",
                }
            if any(k in t for k in ["room", "ห้องจริง", "เดโม", "บอร์ดสด", "lab"]):
                return {
                    "action": "switch_profile",
                    "params": {"profile": "room"},
                    "reply": "สลับเป็นโหมด Live Lab / ห้องจริง (20–36.5°C) สำหรับทดสอบบอร์ดสดเรียบร้อยครับ",
                    "_engine": "Local Rule/Intent Engine",
                }
            if any(k in t for k in ["cold", "ตู้แช่", "ยา", "วัคซีน"]):
                return {
                    "action": "switch_profile",
                    "params": {"profile": "coldchain"},
                    "reply": "สลับเป็นโหมด Cold Chain ตู้แช่ยา/วัคซีน (2–8°C มาตรฐาน GMP) เรียบร้อยครับ",
                    "_engine": "Local Rule/Intent Engine",
                }

        # 3. Crisis simulation
        if any(k in t for k in ["จำลอง", "simulate", "ทดสอบวิกฤต"]):
            if any(k in t for k in ["ดับ", "พัง", "failure", "คอม"]):
                return {
                    "action": "simulate_crisis",
                    "params": {"scenario": "failure"},
                    "reply": "จำลองเหตุการณ์คอมเพรสเซอร์ดับ (Cooling Failure) ส่งเข้าสู่ระบบแล้วครับ",
                    "_engine": "Local Rule/Intent Engine",
                }
            if any(k in t for k in ["แผ่ว", "เตือน", "warning", "warn"]):
                return {
                    "action": "simulate_crisis",
                    "params": {"scenario": "warning"},
                    "reply": "จำลองเหตุการณ์แอร์เริ่มแผ่ว (Predictive Warning) ส่งเข้าสู่ระบบแล้วครับ",
                    "_engine": "Local Rule/Intent Engine",
                }
            if any(k in t for k in ["กระแทก", "เขย่า", "slam", "shock"]):
                return {
                    "action": "simulate_crisis",
                    "params": {"scenario": "door_slam"},
                    "reply": "จำลองเหตุการณ์แรงกระแทก/เปิดประตูแรง (MPU6050 Shock) แล้วครับ",
                    "_engine": "Local Rule/Intent Engine",
                }
            if any(k in t for k in ["รบกวน", "glitch", "สไปก์", "spike"]):
                return {
                    "action": "simulate_crisis",
                    "params": {"scenario": "glitch"},
                    "reply": "จำลองเหตุการณ์สัญญาณรบกวน (Sensor Glitch) ส่งเข้าสู่ระบบแล้วครับ",
                    "_engine": "Local Rule/Intent Engine",
                }
            return {
                "action": "simulate_crisis",
                "params": {"scenario": "normal"},
                "reply": "จำลองค่าสภาวะปกติส่งเข้าสู่ระบบแล้วครับ",
                "_engine": "Local Rule/Intent Engine",
            }

        # 4. CAPA report
        if any(k in t for k in ["capa", "รายงาน", "สาเหตุ", "วิธีแก้", "report"]):
            return {
                "action": "get_capa_report",
                "params": {},
                "reply": "สรุปรายงานวิเคราะห์สาเหตุและแนวทางแก้ไข CAPA ให้แล้วครับ",
                "_engine": "Local Rule/Intent Engine",
            }

        # 5. Default status summary
        return {
            "action": "get_status",
            "params": {},
            "reply": (
                f"สถานะล่าสุด ({ai_state.get('profile_name')}): "
                f"อุณหภูมิ {ai_state.get('current_temp')}°C, ความชื้น {ai_state.get('current_humid')}%, "
                f"ความดัน {ai_state.get('current_pressure')} hPa, แรงสั่น {ai_state.get('current_vib_g')}g | "
                f"ความเสี่ยง: {ai_state.get('risk_level')} (Health Score {ai_state.get('health_score')}/100)"
            ),
            "_engine": "Local Rule/Intent Engine",
        }

    def process(self, user_message: str, ai_state: dict, executors: dict) -> dict:
        # Try Ollama first; gracefully fallback to local deterministic intent parser
        intent = self._call_ollama(user_message, ai_state)
        if not intent:
            intent = self._fallback_parse(user_message, ai_state)

        action = str(intent.get("action", "get_status"))
        params = intent.get("params")
        if not isinstance(params, dict):
            params = {}
        reply = str(intent.get("reply", ""))
        engine_used = intent.get("_engine", "Local Engine")

        # Validate through Deterministic Safety Guardrails
        allowed, guardrail_msg = self.guardrails.validate(action, params, ai_state)

        exec_result = None
        if allowed:
            fn = executors.get(action)
            if fn:
                exec_result = fn(params)
                if action == "get_capa_report" and isinstance(exec_result, dict):
                    reply = exec_result.get("summary_text", reply)
                elif action == "get_status" and not reply:
                    reply = (
                        f"อุณหภูมิ {ai_state.get('current_temp')}°C | ความชื้น {ai_state.get('current_humid')}% | "
                        f"สถานะ {ai_state.get('risk_level')}"
                    )
        else:
            reply = f"🛡️ {guardrail_msg}"

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
