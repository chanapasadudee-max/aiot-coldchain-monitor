"""
AI Incident Advisor & Root Cause Analyzer
File: incident_advisor.py
Author: Chanapa Sadudee (6610680214)

โมดูล AI ที่ทำหน้าที่เป็น "ผู้เชี่ยวชาญวิศวกรรมอัจฉริยะ (AI Plant Engineer Advisor)"
สังเคราะห์รายงานการตรวจพบความผิดปกติ แนะนำมาตรการแก้ไขเร่งด่วน (CAPA - Corrective and Preventive Action)
ตามมาตรฐาน GMP / GDP / ISO 22000
"""

import os
from datetime import datetime

class IncidentAdvisor:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "")

    def generate_report(self, anomaly_info: dict) -> dict:
        temp = anomaly_info.get("current_temp", 0.0)
        humid = anomaly_info.get("current_humid", 0.0)
        risk = anomaly_info.get("risk_level", "NORMAL")
        slope = anomaly_info.get("slope_per_step", 0.0)
        ettf = anomaly_info.get("ettf_seconds")
        reasons = ", ".join(anomaly_info.get("anomaly_reasons", []))

        # ประเมินสาเหตุที่เป็นไปได้ (Root Cause Hypothesis)
        possible_causes = []
        action_steps = []

        if slope > 0.15 and humid > 70.0:
            cause = "ประตูห้องเย็น/ตู้แช่เปิดทิ้งไว้ หรือขอบยางประตูปิดไม่สนิท (Door Ajar / Seal Breach)"
            possible_causes.append(cause)
            action_steps.extend([
                "ตรวจสอบกลอนประตูตู้แช่ทันทีและดันให้สนิท",
                "ตรวจสอบขอบยางตู้แช่ว่ามีน้ำแข็งเกาะหรือรอยรั่วหรือไม่",
                "หลีกเลี่ยงการเปิดประตูตู้แช่จนกว่าอุณหภูมิจะลดลงสู่ระดับปกติ"
            ])
        elif slope > 0.15:
            cause = "คอมเพรสเซอร์ทำความเย็นหยุดทำงาน หรือระบบระบายความร้อนขัดข้อง (Cooling Compressor Trip)"
            possible_causes.append(cause)
            action_steps.extend([
                "ตรวจสอบเบรกเกอร์ไฟฟ้าหลักของชุดคอมเพรสเซอร์",
                "สลับไปใช้ระบบทำความเย็นสำรอง (Redundant Unit B)",
                "หากอุณหภูมิเกิน 8°C ให้นำยาและวัคซีนย้ายไปยังตู้สำรองฉุกเฉินทันที"
            ])
        elif temp < 2.0:
            cause = "เทอร์โมสตัทค้าง หรือวาล์วน้ำยาทำความเย็นเปิดค้างจนเกิดภาวะเยือกแข็ง (Overcooling Risk)"
            possible_causes.append(cause)
            action_steps.extend([
                "ปรับตั้งค่าชุดควบคุมอุณหภูมิให้กลับสู่ 4.0°C",
                "ตรวจสอบเซ็นเซอร์วัดน้ำแข็งคอยล์เย็น (Defrost Sensor)"
            ])
        else:
            cause = "สภาวะการทำงานปกติ หรือมีการรบกวนสัญญาณชั่วคราว"
            possible_causes.append(cause)
            action_steps.append("เฝ้าสังเกตการณ์กราฟอย่างต่อเนื่อง")

        # สร้างข้อความสรุปสำหรับส่งเข้า Telegram Alert
        now_time = datetime.now().strftime("%H:%M:%S")
        if risk == "CRITICAL":
            summary = (
                f"🚨 **[วิกฤตความเย็นระดับ CRITICAL]** 🚨\n"
                f"⏰ เวลา: {now_time}\n"
                f"🌡️ อุณหภูมิ: {temp}°C | 💧 ความชื้น: {humid}%\n"
                f"🔍 สาเหตุที่คาดการณ์: {possible_causes[0]}\n"
                f"⚠️ อาการ: {reasons}\n"
                f"🛠️ คำแนะนำด่วน:\n• " + "\n• ".join(action_steps[:2])
            )
        elif risk == "WARNING":
            ettf_str = f"เหลือเวลาประมาณ {ettf:.0f} วินาที ก่อนแตะ 8°C" if ettf else "กรุณาตรวจสอบระบบทำความเย็น"
            summary = (
                f"⚠️ **[แจ้งเตือนเฝ้าระวัง WARNING]**\n"
                f"⏰ เวลา: {now_time}\n"
                f"🌡️ อุณหภูมิ: {temp}°C (อัตราการเพิ่ม: +{slope:.2f}°C/step)\n"
                f"⏳ การคาดการณ์: {ettf_str}\n"
                f"🔍 สาเหตุที่คาดการณ์: {possible_causes[0]}\n"
                f"🛠️ สิ่งที่ต้องทำ: {action_steps[0]}"
            )
        else:
            summary = f"🟢 ระบบทำงานปกติ: อุณหภูมิ {temp}°C อยู่ในเกณฑ์มาตรฐานความปลอดภัย"

        return {
            "risk_level": risk,
            "root_cause": possible_causes[0],
            "action_steps": action_steps,
            "summary_text": summary
        }
