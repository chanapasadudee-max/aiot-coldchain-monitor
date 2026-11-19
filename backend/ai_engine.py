"""
AI Anomaly Detection Engine — Multi-Sensor & Multi-Profile Edition
File: ai_engine.py
Author: Chanapa Sadudee (6610680214)

โมเดลปัญญาประดิษฐ์วิเคราะห์สภาวะความผิดปกติแบบ Real-Time:
  1. Multi-Profile Support: coldchain (2-8°C), server (18-24°C), room (20-36°C)
  2. Statistical Z-Score Outlier Detection (ตรวจจับ Sensor Glitch)
  3. Rolling Linear Slope Analysis (พยากรณ์คอมเพรสเซอร์ดับล่วงหน้า)
  4. MPU6050 Vibration & Shock Detection (ตรวจจับการกระแทก/เปิดประตูแรง)
  5. Estimated Time to Failure (ETTF) + Facility Health Score (0-100)
"""

import math
from collections import deque
from datetime import datetime

FACILITY_PROFILES = {
    "coldchain": {
        "name": "Cold Chain (ตู้แช่ยา/วัคซีน GMP)",
        "safe_min": 2.0,
        "safe_max": 8.0,
        "humid_min": 45.0,
        "humid_max": 75.0,
        "vib_warn": 0.35,
    },
    "server": {
        "name": "Server Room / Data Center (ASHRAE)",
        "safe_min": 18.0,
        "safe_max": 24.0,
        "humid_min": 35.0,
        "humid_max": 60.0,
        "vib_warn": 0.30,
    },
    "room": {
        "name": "Live Lab / Ambient Room (โหมดเดโมบอร์ดสด)",
        "safe_min": 20.0,
        "safe_max": 36.5,
        "humid_min": 30.0,
        "humid_max": 80.0,
        "vib_warn": 0.35,
    },
}


class IndustrialAnomalyEngine:
    def __init__(self, window_size: int = 15, profile: str = "coldchain"):
        self.window_size = window_size
        self.profile_key = profile if profile in FACILITY_PROFILES else "coldchain"
        self._apply_profile()
        self.history = deque(maxlen=window_size)
        self.timestamps = deque(maxlen=window_size)

    def _apply_profile(self):
        cfg = FACILITY_PROFILES[self.profile_key]
        self.safe_min = cfg["safe_min"]
        self.safe_max = cfg["safe_max"]
        self.humid_min = cfg["humid_min"]
        self.humid_max = cfg["humid_max"]
        self.vib_warn = cfg["vib_warn"]
        self.profile_name = cfg["name"]

    def set_profile(self, profile: str) -> dict:
        if profile not in FACILITY_PROFILES:
            raise ValueError(f"Unknown profile: {profile}. Choose from {list(FACILITY_PROFILES.keys())}")
        self.profile_key = profile
        self._apply_profile()
        return self.get_profile_info()

    def get_profile_info(self) -> dict:
        return {
            "profile": self.profile_key,
            "name": self.profile_name,
            "safe_range": [self.safe_min, self.safe_max],
            "humid_range": [self.humid_min, self.humid_max],
            "vib_warn": self.vib_warn,
        }

    def feed(
        self,
        temp: float,
        humid: float,
        pressure: float = 1013.25,
        vib_g: float = 0.0,
        shock: bool = False,
        sensors: list | None = None,
        ts_str: str | None = None,
    ) -> dict:
        self.history.append((temp, humid, pressure, vib_g))
        self.timestamps.append(datetime.now())

        count = len(self.history)
        temps = [row[0] for row in self.history]

        # 1. Moving Mean & Std
        mean_temp = sum(temps) / count
        variance = sum((t - mean_temp) ** 2 for t in temps) / count if count > 1 else 0.0
        std_temp = math.sqrt(variance)

        # 2. Z-Score
        z_score = (temp - mean_temp) / std_temp if std_temp > 0.05 else 0.0

        # 3. Rolling Linear Regression Slope
        slope_per_step = 0.0
        if count >= 3:
            x_bar = (count - 1) / 2.0
            y_bar = mean_temp
            num = sum((i - x_bar) * (temps[i] - y_bar) for i in range(count))
            den = sum((i - x_bar) ** 2 for i in range(count))
            slope_per_step = num / den if den != 0 else 0.0

        # 4. Risk Level Classification & Health Score (0-100)
        risk_level = "NORMAL"
        anomaly_reasons = []
        health_score = 100

        if temp > self.safe_max:
            risk_level = "CRITICAL"
            over = temp - self.safe_max
            health_score -= min(65, int(35 + over * 8))
            anomaly_reasons.append(
                f"อุณหภูมิเกินขีดจำกัดปลอดภัย ({temp:.2f}°C > {self.safe_max:.1f}°C)"
            )
        elif temp < self.safe_min:
            risk_level = "CRITICAL"
            under = self.safe_min - temp
            health_score -= min(60, int(30 + under * 8))
            anomaly_reasons.append(
                f"อุณหภูมิต่ำเกินขีดจำกัด ({temp:.2f}°C < {self.safe_min:.1f}°C)"
            )

        if slope_per_step > 0.18:
            if risk_level != "CRITICAL":
                risk_level = "WARNING"
            health_score -= 22
            anomaly_reasons.append(
                f"ความชันอุณหภูมิไต่ขึ้นเร็วผิดปกติ (+{slope_per_step:.2f}°C/step) เสี่ยงระบบทำความเย็นขัดข้อง"
            )
        elif abs(z_score) > 2.8 and count >= 5:
            if risk_level != "CRITICAL":
                risk_level = "WARNING"
            health_score -= 15
            anomaly_reasons.append(f"พบค่าเบี่ยงเบนทางสถิติสูงผิดปกติ (Z-Score = {z_score:.2f})")

        # MPU6050 Vibration / Shock Anomaly
        if shock or vib_g >= self.vib_warn:
            if risk_level != "CRITICAL":
                risk_level = "WARNING"
            health_score -= 20
            anomaly_reasons.append(
                f"ตรวจพบแรงสั่นสะเทือน/แรงกระแทกผิดปกติ ({vib_g:.2f}g) เสี่ยงเปิดประตูแรงหรือคอมเพรสเซอร์สั่น"
            )

        # Humidity out-of-band minor penalty
        if humid > self.humid_max or humid < self.humid_min:
            health_score -= 8

        health_score = max(0, min(100, health_score))

        # 5. Estimated Time to Failure (ETTF)
        ettf_seconds = None
        if slope_per_step > 0.05 and temp < self.safe_max:
            remaining_temp = self.safe_max - temp
            steps_left = remaining_temp / slope_per_step
            ettf_seconds = max(0.0, round(steps_left * 2.0, 1))

        return {
            "profile": self.profile_key,
            "profile_name": self.profile_name,
            "current_temp": round(temp, 2),
            "current_humid": round(humid, 2),
            "current_pressure": round(pressure, 2),
            "current_vib_g": round(vib_g, 3),
            "shock_detected": bool(shock or vib_g >= self.vib_warn),
            "sensors": sensors or ["HTS221"],
            "moving_mean": round(mean_temp, 2),
            "std_dev": round(std_temp, 2),
            "z_score": round(z_score, 2),
            "slope_per_step": round(slope_per_step, 3),
            "risk_level": risk_level,
            "health_score": health_score,
            "anomaly_detected": risk_level != "NORMAL",
            "anomaly_reasons": anomaly_reasons,
            "ettf_seconds": ettf_seconds,
            "safe_range": [self.safe_min, self.safe_max],
        }
