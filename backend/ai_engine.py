"""
AI Anomaly Detection Engine
File: ai_engine.py
Author: Chanapa Sadudee (6610680214)

โมเดลปัญญาประดิษฐ์วิเคราะห์สภาวะความผิดปกติของอุณหภูมิและความชื้นแบบ Real-Time
ประกอบด้วย:
  1. Statistical Z-Score Outlier Detection (ตรวจจับค่ากระโดดผิดปกติ)
  2. Rolling Slope & Rate-of-Change Analysis (ตรวจจับคอมเพรสเซอร์ดับล่วงหน้า)
  3. Risk Classification (NORMAL, WARNING, CRITICAL)
  4. Estimated Time to Failure (ETTF) คำนวณเวลาที่เหลือก่อนยา/ระบบจะเสียหาย
"""

import math
from collections import deque
from datetime import datetime

class IndustrialAnomalyEngine:
    def __init__(self, window_size: int = 15, safe_min: float = 2.0, safe_max: float = 8.0):
        self.window_size = window_size
        self.safe_min = safe_min
        self.safe_max = safe_max
        self.history = deque(maxlen=window_size)
        self.timestamps = deque(maxlen=window_size)

    def feed(self, temp: float, humid: float, ts_str: str = None) -> dict:
        self.history.append((temp, humid))
        self.timestamps.append(datetime.now())

        count = len(self.history)
        temps = [t for t, h in self.history]

        # 1. ค่าเฉลี่ยและส่วนเบี่ยงเบนมาตรฐาน (Moving Mean & Std)
        mean_temp = sum(temps) / count
        variance = sum((t - mean_temp) ** 2 for t in temps) / count if count > 1 else 0.0
        std_temp = math.sqrt(variance)

        # 2. คำนวณ Z-Score ของค่าล่าสุด
        z_score = (temp - mean_temp) / std_temp if std_temp > 0.05 else 0.0

        # 3. คำนวณ Trend Slope (ความชันของอุณหภูมิในช่วงสั้นๆ)
        slope_per_step = 0.0
        if count >= 3:
            # คำนวณ Simple Linear Regression Slope
            x_bar = (count - 1) / 2.0
            y_bar = mean_temp
            num = sum((i - x_bar) * (temps[i] - y_bar) for i in range(count))
            den = sum((i - x_bar) ** 2 for i in range(count))
            slope_per_step = num / den if den != 0 else 0.0

        # 4. ประเมินระดับความเสี่ยง (Risk Level Classification)
        risk_level = "NORMAL"
        anomaly_reasons = []

        # เช็กขอบเขตวิกฤต (Hard Threshold)
        if temp > self.safe_max:
            risk_level = "CRITICAL"
            anomaly_reasons.append(f"อุณหภูมิเกินขีดจำกัดความปลอดภัย ({temp:.2f}°C > {self.safe_max}°C)")
        elif temp < self.safe_min:
            risk_level = "CRITICAL"
            anomaly_reasons.append(f"อุณหภูมิต่ำเกินไปจนเสี่ยงเป็นน้ำแข็ง ({temp:.2f}°C < {self.safe_min}°C)")

        # เช็กความชัน (Predictive Slope Analysis)
        # หากอุณหภูมิยังไม่เกิน 8°C แต่ไต่ระดับขึ้นเร็วต่อเนื่อง (slope > 0.15 ต่อสเต็ป)
        if slope_per_step > 0.18 and risk_level != "CRITICAL":
            risk_level = "WARNING"
            anomaly_reasons.append(f"ความชันอุณหภูมิสูงผิดปกติ (+{slope_per_step:.2f}°C/step) เสี่ยงระบบทำความเย็นขัดข้อง")
        elif abs(z_score) > 2.8 and count >= 5:
            if risk_level != "CRITICAL":
                risk_level = "WARNING"
            anomaly_reasons.append(f"พบค่าเบี่ยงเบนทางสถิติสูงผิดปกติ (Z-Score = {z_score:.2f})")

        # 5. คำนวณเวลาที่เหลือก่อนวิกฤต (Estimated Time to Failure - ETTF)
        ettf_seconds = None
        if slope_per_step > 0.05 and temp < self.safe_max:
            remaining_temp = self.safe_max - temp
            steps_left = remaining_temp / slope_per_step
            # สมมุติช่วงเวลา 2 วินาทีต่อสเต็ป
            ettf_seconds = max(0.0, round(steps_left * 2.0, 1))

        return {
            "current_temp": round(temp, 2),
            "current_humid": round(humid, 2),
            "moving_mean": round(mean_temp, 2),
            "std_dev": round(std_temp, 2),
            "z_score": round(z_score, 2),
            "slope_per_step": round(slope_per_step, 3),
            "risk_level": risk_level,
            "anomaly_detected": risk_level != "NORMAL",
            "anomaly_reasons": anomaly_reasons,
            "ettf_seconds": ettf_seconds,
            "safe_range": [self.safe_min, self.safe_max]
        }
