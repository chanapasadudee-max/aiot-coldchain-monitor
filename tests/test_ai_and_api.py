"""
Automated Unit & Integration Test Suite — AI Engine, Guardrails & FastAPI
File: tests/test_ai_and_api.py
Author: Chanapa Sadudee (6610680214)
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from fastapi.testclient import TestClient
from ai_engine import IndustrialAnomalyEngine
from ai_copilot import SafetyGuardrails
import app as backend_app


def test_ai_engine_profiles_and_anomalies():
    engine = IndustrialAnomalyEngine(window_size=15, profile="coldchain")
    # 1. Normal cold chain
    for _ in range(6):
        res = engine.feed(4.2, 60.0, pressure=1012.5, vib_g=0.02, shock=False)
    assert res["risk_level"] == "NORMAL", f"Expected NORMAL, got {res['risk_level']}"
    assert res["health_score"] == 100

    # 2. Predictive slope warning (still < 8.0C, but climbing fast!)
    for t in [4.6, 5.1, 5.7, 6.4, 7.1]:
        res = engine.feed(t, 64.0, pressure=1012.0, vib_g=0.05, shock=False)
    assert res["risk_level"] == "WARNING", f"Expected WARNING, got {res['risk_level']}"
    assert res["slope_per_step"] > 0.18
    assert res["ettf_seconds"] is not None and res["ettf_seconds"] > 0

    # 3. Hard critical threshold (> 8.0C)
    res = engine.feed(9.5, 72.0, pressure=1011.0, vib_g=0.05, shock=False)
    assert res["risk_level"] == "CRITICAL"
    assert res["health_score"] < 60

    # 4. Vibration / Shock detection (MPU6050)
    engine_vib = IndustrialAnomalyEngine(window_size=10, profile="coldchain")
    res_shock = engine_vib.feed(4.3, 60.0, pressure=1008.0, vib_g=0.88, shock=True)
    assert res_shock["risk_level"] == "WARNING"
    assert res_shock["shock_detected"] is True

    # 5. Profile switch to live room (34.5C is safe in room mode!)
    engine_room = IndustrialAnomalyEngine(window_size=10, profile="room")
    res_room = engine_room.feed(34.5, 50.0, pressure=1008.5, vib_g=0.02, shock=False)
    assert res_room["risk_level"] == "NORMAL"
    print("[PASS] test_ai_engine_profiles_and_anomalies")


def test_safety_guardrails():
    gr = SafetyGuardrails()
    critical_state = {"risk_level": "CRITICAL"}
    normal_state = {"risk_level": "NORMAL"}

    # Must BLOCK turning off LED during CRITICAL without force override
    allowed, note = gr.validate("set_led", {"mode": "off", "force": False}, critical_state)
    assert allowed is False and "BLOCKED" in note

    # Must ALLOW turning off LED during CRITICAL when explicitly forced
    allowed_f, _ = gr.validate("set_led", {"mode": "off", "force": True}, critical_state)
    assert allowed_f is True

    # Must ALLOW turning off LED during NORMAL
    allowed_n, _ = gr.validate("set_led", {"mode": "off", "force": False}, normal_state)
    assert allowed_n is True

    # Must BLOCK invalid profile
    allowed_p, _ = gr.validate("switch_profile", {"profile": "mars_base"}, normal_state)
    assert allowed_p is False
    print("[PASS] test_safety_guardrails")


def test_fastapi_endpoints():
    client = TestClient(backend_app.app)

    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "online"

    # Switch profile to coldchain
    r = client.post("/api/profile", json={"profile": "coldchain"})
    assert r.status_code == 200
    assert r.json()["profile"]["profile"] == "coldchain"

    # Simulate failure -> CRITICAL
    r = client.post("/api/simulate-scenario?scenario=failure")
    assert r.status_code == 200

    # Test Guardrail via /api/chat (should block turning off LED when CRITICAL!)
    backend_app.latest_ai_result["risk_level"] = "CRITICAL"
    r = client.post("/api/chat", json={"message": "ปิดไฟ"})
    assert r.status_code == 200
    data = r.json()
    assert data["action"] == "set_led"
    assert data["guardrail_allowed"] is False

    # Test /api/audit recorded the blocked attempt
    r = client.get("/api/audit")
    assert r.status_code == 200
    assert len(r.json()["audit_log"]) >= 1

    # Test GMP CSV export
    r = client.get("/api/export.csv")
    assert r.status_code == 200
    assert "timestamp_utc" in r.text
    print("[PASS] test_fastapi_endpoints")


if __name__ == "__main__":
    test_ai_engine_profiles_and_anomalies()
    test_safety_guardrails()
    test_fastapi_endpoints()
    print("\n=== ALL UNIT & API TESTS PASSED (3/3) ===")
