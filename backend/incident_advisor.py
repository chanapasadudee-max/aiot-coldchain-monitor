"""
AI Incident Advisor & Root Cause Analyzer (CAPA Standard)
File: incident_advisor.py
Author: Chanapa Sadudee (6610680214)

วิเคราะห์สาเหตุความผิดปกติจาก Multi-Sensor (Temp, Humid, Pressure, Vibration/Shock)
และเสนอมาตรการแก้ไขเร่งด่วน (CAPA - Corrective and Preventive Action)
"""

from datetime import datetime


class IncidentAdvisor:
    def generate_report(self, anomaly_info: dict) -> dict:
        temp = anomaly_info.get("current_temp", 0.0)
        humid = anomaly_info.get("current_humid", 0.0)
        pressure = anomaly_info.get("current_pressure", 1013.25)
        vib_g = anomaly_info.get("current_vib_g", 0.0)
        shock = anomaly_info.get("shock_detected", False)
        risk = anomaly_info.get("risk_level", "NORMAL")
        slope = anomaly_info.get("slope_per_step", 0.0)
        ettf = anomaly_info.get("ettf_seconds")
        safe_min, safe_max = anomaly_info.get("safe_range", [2.0, 8.0])
        profile_name = anomaly_info.get("profile_name", "Cold Chain")
        reasons = ", ".join(anomaly_info.get("anomaly_reasons", []))

        possible_causes = []
        action_steps = []

        if shock or vib_g >= 0.35:
            possible_causes.append(
                f"ตรวจพบแรงสั่นสะเทือน/แรงกระแทก ({vib_g:.2f}g) จาก MPU6050 — อาจมีการเปิด-ปิดประตูแรง การเคลื่อนย้าย หรือคอมเพรสเซอร์สั่นผิดปกติ"
            )
            action_steps.extend([
                "ตรวจสอบกล้องวงจรปิดหรือการเข้า-ออกพื้นที่ตู้แช่/ห้องเครื่อง",
                "ตรวจสอบฐานยางรองคอมเพรสเซอร์และลูกปืนพัดลมระบายความร้อน",
                "ตรวจสอบว่าประตูปิดสนิทและอุณหภูมิยังเสถียรหรือไม่",
            ])
        elif slope > 0.15 and humid > 70.0:
            possible_causes.append("ประตูห้องเย็น/ตู้แช่เปิดทิ้งไว้ หรือขอบยางประตูปิดไม่สนิท (Door Ajar / Seal Breach)")
            action_steps.extend([
                "ตรวจสอบกลอนประตูตู้แช่ทันทีและดันให้สนิท",
                "ตรวจสอบขอบยางตู้แช่ว่ามีน้ำแข็งเกาะหรือรอยรั่วหรือไม่",
                "งดเปิดประตูซ้ำจนกว่าอุณหภูมิจะกลับเข้าสู่ช่วงปลอดภัย",
            ])
        elif slope > 0.15 or temp > safe_max:
            possible_causes.append("ระบบทำความเย็นขัดข้อง/คอมเพรสเซอร์หยุดทำงาน (Cooling Failure / Overload)")
            action_steps.extend([
                "ตรวจสอบเบรกเกอร์ไฟฟ้าหลักและสถานะคอมเพรสเซอร์ทันที",
                "สลับไปใช้ชุดทำความเย็นสำรอง (Redundant Unit B)",
                f"หากอุณหภูมิเกิน {safe_max:.1f}°C เกิน 15 นาที ให้ย้ายสินค้า/ยาไปตู้สำรองฉุกเฉิน",
            ])
        elif temp < safe_min:
            possible_causes.append("เทอร์โมสตัทค้างหรือน้ำยาทำความเย็นจ่ายเกิน (Overcooling / Freezing Risk)")
            action_steps.extend([
                f"ปรับชุดควบคุมอุณหภูมิกลับสู่ค่ากลาง ({(safe_min + safe_max)/2:.1f}°C)",
                "ตรวจสอบเซ็นเซอร์ละลายน้ำแข็ง (Defrost Sensor)",
            ])
        else:
            possible_causes.append("สภาวะการทำงานปกติ ไม่มีสัญญาณความผิดปกติ")
            action_steps.append("เฝ้าสังเกตการณ์กราฟและระบบอย่างต่อเนื่อง")

        now_time = datetime.now().strftime("%H:%M:%S")
        if risk == "CRITICAL":
            summary = (
                f"🚨 **[วิกฤตความเย็นระดับ CRITICAL — {profile_name}]**\n"
                f"⏰ เวลา: {now_time}\n"
                f"🌡️ อุณหภูมิ: {temp:.2f}°C (เกณฑ์ {safe_min}-{safe_max}°C) | 💧 ความชื้น: {humid:.1f}%\n"
                f"🧭 ความดัน: {pressure:.1f} hPa | 📳 แรงสั่น: {vib_g:.3f}g\n"
                f"🔍 สาเหตุที่คาดการณ์: {possible_causes[0]}\n"
                f"⚠️ อาการ: {reasons}\n"
                f"🛠️ มาตรการ CAPA เร่งด่วน:\n• " + "\n• ".join(action_steps[:3])
            )
        elif risk == "WARNING":
            ettf_str = f"เหลือเวลาประมาณ {ettf:.0f} วินาที ก่อนแตะ {safe_max:.1f}°C" if ettf else "กรุณาตรวจสอบระบบทันที"
            summary = (
                f"⚠️ **[แจ้งเตือนเฝ้าระวัง WARNING — {profile_name}]**\n"
                f"⏰ เวลา: {now_time}\n"
                f"🌡️ อุณหภูมิ: {temp:.2f}°C (Slope: {slope:+.3f}°C/step) | 📳 แรงสั่น: {vib_g:.3f}g\n"
                f"⏳ พยากรณ์ ETTF: {ettf_str}\n"
                f"🔍 สาเหตุที่คาดการณ์: {possible_causes[0]}\n"
                f"🛠️ แนวทางปฏิบัติ: {action_steps[0]}"
            )
        else:
            summary = (
                f"🟢 **ระบบทำงานปกติ ({profile_name})**\n"
                f"🌡️ {temp:.2f}°C | 💧 {humid:.1f}% | 🧭 {pressure:.1f} hPa | 📳 {vib_g:.3f}g"
            )

        return {
            "risk_level": risk,
            "profile": profile_name,
            "root_cause": possible_causes[0],
            "action_steps": action_steps,
            "summary_text": summary,
        }
