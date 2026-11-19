"""
AIoT Industrial Cold Chain Backend Service — Full-Stack Edition
File: app.py
Author: Chanapa Sadudee (6610680214)

บริการ Backend หลัก:
  - Subscribe MQTT ทั้ง tse/cn466/chanapa/telemetry และ tse/cn466/chanapa (รองรับบอร์ดจริง)
  - Publish คำสั่งควบคุมไฟ NeoPixel RGB LED ไปยัง tse/cn466/chanapa/cmd
  - เก็บข้อมูลลง SQLite (coldchain.db) พร้อม Export GMP/FDA CSV
  - Multi-Profile AI Anomaly Engine (Slope, Z-Score, ETTF, Vibration Shock, Health Score)
  - Local Ollama AI Copilot (qwen2.5) + Deterministic Safety Guardrails + Audit Log
"""

import csv
import io
import json
import os
import random
import sqlite3
import threading
from collections import deque
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

import paho.mqtt.client as mqtt
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ai_copilot import AICopilot
from ai_engine import FACILITY_PROFILES, IndustrialAnomalyEngine
from incident_advisor import IncidentAdvisor

# ---------------- Configuration ----------------
MQTT_HOST = os.getenv("MQTT_HOST", "broker.emqx.io")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC_TELEMETRY = os.getenv("MQTT_TOPIC", "tse/cn466/chanapa/telemetry")
MQTT_TOPIC_LEGACY = os.getenv("MQTT_TOPIC_LEGACY", "tse/cn466/chanapa")
MQTT_TOPIC_CMD = os.getenv("MQTT_TOPIC_CMD", "tse/cn466/chanapa/cmd")
DB_PATH = os.getenv("DB_PATH", str(Path(__file__).parent / "coldchain.db"))
PORT = int(os.getenv("PORT", "5000"))

BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR.parent / "ui" / "static"

ai_engine = IndustrialAnomalyEngine(window_size=15, profile="coldchain")
advisor = IncidentAdvisor()
copilot = AICopilot()

# ---------------- SQLite Database ----------------
db_lock = threading.Lock()
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
conn.execute(
    """CREATE TABLE IF NOT EXISTS telemetry (
           id INTEGER PRIMARY KEY AUTOINCREMENT,
           ts TEXT NOT NULL,
           node_id TEXT NOT NULL,
           temp REAL NOT NULL,
           humid REAL NOT NULL,
           pressure REAL DEFAULT 1013.25,
           vib_g REAL DEFAULT 0.0,
           shock INTEGER DEFAULT 0,
           risk_level TEXT NOT NULL,
           health_score INTEGER DEFAULT 100,
           slope REAL NOT NULL,
           z_score REAL NOT NULL,
           scenario TEXT
       )"""
)
# Safe schema migration for existing DBs
existing_cols = {row[1] for row in conn.execute("PRAGMA table_info(telemetry)").fetchall()}
for col_name, col_def in [
    ("pressure", "REAL DEFAULT 1013.25"),
    ("vib_g", "REAL DEFAULT 0.0"),
    ("shock", "INTEGER DEFAULT 0"),
    ("health_score", "INTEGER DEFAULT 100"),
]:
    if col_name not in existing_cols:
        conn.execute(f"ALTER TABLE telemetry ADD COLUMN {col_name} {col_def}")
conn.commit()


def save_telemetry(node_id: str, temp: float, humid: float, pressure: float, vib_g: float, shock: bool, ai_res: dict, scenario: str = "live"):
    with db_lock:
        conn.execute(
            """INSERT INTO telemetry (ts, node_id, temp, humid, pressure, vib_g, shock, risk_level, health_score, slope, z_score, scenario)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                datetime.now(timezone.utc).isoformat(),
                node_id,
                temp,
                humid,
                pressure,
                vib_g,
                1 if shock else 0,
                ai_res["risk_level"],
                ai_res["health_score"],
                ai_res["slope_per_step"],
                ai_res["z_score"],
                scenario,
            ),
        )
        conn.commit()


def get_latest_record():
    with db_lock:
        return conn.execute(
            """SELECT id, ts, node_id, temp, humid, pressure, vib_g, shock, risk_level, health_score, slope, z_score, scenario
               FROM telemetry ORDER BY id DESC LIMIT 1"""
        ).fetchone()


def get_history_records(limit: int = 40):
    with db_lock:
        return conn.execute(
            """SELECT id, ts, node_id, temp, humid, pressure, vib_g, shock, risk_level, health_score, slope, z_score, scenario
               FROM telemetry ORDER BY id DESC LIMIT ?""",
            (limit,),
        ).fetchall()


# ---------------- MQTT State & Bidirectional Control ----------------
mqtt_connected = threading.Event()
mqtt_client = None
mqtt_log = deque(maxlen=40)
auto_sync_led = True
last_synced_led_mode = "safe"

latest_ai_result = {
    "profile": "coldchain",
    "profile_name": FACILITY_PROFILES["coldchain"]["name"],
    "current_temp": 4.2,
    "current_humid": 60.0,
    "current_pressure": 1013.25,
    "current_vib_g": 0.02,
    "shock_detected": False,
    "sensors": ["HTS221", "BMP280", "MPU6050"],
    "moving_mean": 4.2,
    "std_dev": 0.0,
    "z_score": 0.0,
    "slope_per_step": 0.0,
    "risk_level": "NORMAL",
    "health_score": 100,
    "anomaly_detected": False,
    "anomaly_reasons": [],
    "ettf_seconds": None,
    "safe_range": [2.0, 8.0],
}


def publish_led_command(mode: str, r: int = 0, g: int = 0, b: int = 0) -> dict:
    global last_synced_led_mode
    payload = {"cmd": "set_led", "mode": mode, "r": r, "g": g, "b": b}
    if mqtt_client and mqtt_connected.is_set():
        mqtt_client.publish(MQTT_TOPIC_CMD, json.dumps(payload))
    last_synced_led_mode = mode
    mqtt_log.appendleft({
        "ts": datetime.now(timezone.utc).isoformat(),
        "dir": "TX_CMD",
        "topic": MQTT_TOPIC_CMD,
        "payload": payload,
    })
    return payload


def on_connect(client, userdata, flags, reason_code, properties=None):
    print(f"[MQTT] Connected (rc={reason_code}). Subscribing to {MQTT_TOPIC_TELEMETRY} & {MQTT_TOPIC_LEGACY}")
    client.subscribe(MQTT_TOPIC_TELEMETRY)
    client.subscribe(MQTT_TOPIC_LEGACY)
    mqtt_connected.set()


def on_message(client, userdata, msg):
    global latest_ai_result
    try:
        raw = msg.payload.decode()
        data = json.loads(raw)
        if "ack" in data:
            mqtt_log.appendleft({
                "ts": datetime.now(timezone.utc).isoformat(),
                "dir": "RX_ACK",
                "topic": msg.topic,
                "payload": data,
            })
            return
        if "temp" not in data or "humid" not in data:
            return

        node_id = str(data.get("node_id", "cucumber-ris-01"))
        temp = float(data["temp"])
        humid = float(data["humid"])
        pressure = float(data.get("pressure", 1013.25))
        vib_g = float(data.get("vib_g", 0.0))
        shock = bool(data.get("shock", False))
        sensors = data.get("sensors", ["HTS221"])
        scenario = str(data.get("scenario", "hardware_live"))
    except Exception:
        return

    mqtt_log.appendleft({
        "ts": datetime.now(timezone.utc).isoformat(),
        "dir": "RX_DATA",
        "topic": msg.topic,
        "payload": data,
    })

    ai_res = ai_engine.feed(temp, humid, pressure=pressure, vib_g=vib_g, shock=shock, sensors=sensors)
    latest_ai_result = ai_res
    save_telemetry(node_id, temp, humid, pressure, vib_g, shock, ai_res, scenario)

    # Auto-sync physical NeoPixel RGB LED on Cucumber board when risk changes
    if auto_sync_led:
        target_led = "safe" if ai_res["risk_level"] == "NORMAL" else (
            "warning" if ai_res["risk_level"] == "WARNING" else "critical"
        )
        if target_led != last_synced_led_mode:
            publish_led_command(target_led)


def start_mqtt():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    client.reconnect_delay_set(min_delay=1, max_delay=20)
    try:
        client.connect_async(MQTT_HOST, MQTT_PORT, keepalive=60)
        client.loop_start()
    except Exception as e:
        print(f"[MQTT] Connect error: {e}")
    return client


# ---------------- FastAPI App ----------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    global mqtt_client
    mqtt_client = start_mqtt()
    yield
    if mqtt_client:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()


app = FastAPI(
    title="AIoT Industrial Cold Chain API",
    description="ระบบเฝ้าระวังตู้แช่ยาและห้อง Server อุตสาหกรรม ด้วย AIoT + บอร์ด Cucumber RIS + Local Ollama Copilot",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class ChatRequest(BaseModel):
    message: str


class LedCommandRequest(BaseModel):
    mode: str = "safe"
    r: int = 0
    g: int = 0
    b: int = 0
    force: bool = False


class ProfileRequest(BaseModel):
    profile: str


def _execute_simulate(scenario: str) -> dict:
    global latest_ai_result
    pressure = round(random.uniform(1011.0, 1014.0), 2)
    vib_g = round(random.uniform(0.01, 0.05), 3)
    shock = False

    if scenario == "failure":
        temp = round(ai_engine.safe_max + random.uniform(1.8, 3.2), 2)
        humid = round(random.uniform(72.0, 82.0), 2)
        vib_g = round(random.uniform(0.12, 0.25), 3)
    elif scenario == "warning":
        temp = round(ai_engine.safe_max - 0.8, 2)
        humid = round(random.uniform(66.0, 74.0), 2)
        # Feed 3 rising points so slope detector triggers Predictive Warning
        for step_t in [temp - 0.9, temp - 0.45]:
            ai_engine.feed(step_t, humid, pressure=pressure, vib_g=vib_g, shock=False)
    elif scenario == "door_slam":
        temp = round((ai_engine.safe_min + ai_engine.safe_max) / 2 + 0.8, 2)
        humid = round(random.uniform(68.0, 78.0), 2)
        pressure = 1007.5
        vib_g = round(random.uniform(0.68, 1.35), 3)
        shock = True
    elif scenario == "glitch":
        temp = round(ai_engine.safe_max + 7.5, 2)
        humid = 60.0
    else:
        mid = (ai_engine.safe_min + ai_engine.safe_max) / 2
        temp = round(random.uniform(mid - 0.7, mid + 0.7), 2)
        humid = round(random.uniform(55.0, 65.0), 2)

    payload = {
        "node_id": "sim-control",
        "temp": temp,
        "humid": humid,
        "pressure": pressure,
        "vib_g": vib_g,
        "shock": shock,
        "sensors": ["HTS221", "BMP280", "MPU6050"],
        "scenario": scenario,
    }
    if mqtt_client and mqtt_connected.is_set():
        mqtt_client.publish(MQTT_TOPIC_TELEMETRY, json.dumps(payload))
    else:
        ai_res = ai_engine.feed(temp, humid, pressure=pressure, vib_g=vib_g, shock=shock, sensors=payload["sensors"])
        latest_ai_result = ai_res
        save_telemetry(payload["node_id"], temp, humid, pressure, vib_g, shock, ai_res, scenario)
    return payload


@app.get("/")
def serve_dashboard():
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "AIoT Backend is running."}


@app.get("/logo.png")
def serve_logo():
    return FileResponse(STATIC_DIR / "logo.png")


@app.get("/logo_dark.png")
def serve_logo_dark():
    return FileResponse(STATIC_DIR / "logo_dark.png")


@app.get("/logo_light.png")
def serve_logo_light():
    return FileResponse(STATIC_DIR / "logo_light.png")


@app.get("/api/health")
def api_health():
    with db_lock:
        count = conn.execute("SELECT COUNT(*) FROM telemetry").fetchone()[0]
    return {
        "status": "online",
        "version": "2.0.0",
        "service": "AIoT Industrial Cold Chain Service",
        "mqtt_broker": MQTT_HOST,
        "mqtt_topics": [MQTT_TOPIC_TELEMETRY, MQTT_TOPIC_LEGACY],
        "mqtt_cmd_topic": MQTT_TOPIC_CMD,
        "mqtt_connected": mqtt_connected.is_set(),
        "profile": ai_engine.get_profile_info(),
        "led_mode": last_synced_led_mode,
        "total_readings": count,
    }


@app.get("/api/latest")
def api_latest():
    row = get_latest_record()
    tele = None
    if row:
        tele = {
            "id": row[0],
            "ts": row[1],
            "node_id": row[2],
            "temp": row[3],
            "humid": row[4],
            "pressure": row[5],
            "vib_g": row[6],
            "shock": bool(row[7]),
            "risk_level": row[8],
            "health_score": row[9],
            "slope": row[10],
            "z_score": row[11],
            "scenario": row[12],
        }
    return {
        "telemetry": tele,
        "ai_evaluation": latest_ai_result,
        "led_mode": last_synced_led_mode,
        "profiles": FACILITY_PROFILES,
    }


@app.get("/api/history")
def api_history(limit: int = 30):
    rows = get_history_records(max(1, min(limit, 200)))
    return [
        {
            "id": r[0],
            "ts": r[1],
            "node_id": r[2],
            "temp": r[3],
            "humid": r[4],
            "pressure": r[5],
            "vib_g": r[6],
            "shock": bool(r[7]),
            "risk_level": r[8],
            "health_score": r[9],
            "slope": r[10],
            "z_score": r[11],
            "scenario": r[12],
        }
        for r in reversed(rows)
    ]


@app.get("/api/incident-report")
def api_incident_report():
    return advisor.generate_report(latest_ai_result)


@app.post("/api/profile")
def api_set_profile(req: ProfileRequest):
    global latest_ai_result
    try:
        info = ai_engine.set_profile(req.profile)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    # Re-evaluate latest reading under new profile immediately
    latest_ai_result = ai_engine.feed(
        latest_ai_result["current_temp"],
        latest_ai_result["current_humid"],
        pressure=latest_ai_result.get("current_pressure", 1013.25),
        vib_g=latest_ai_result.get("current_vib_g", 0.0),
        shock=latest_ai_result.get("shock_detected", False),
        sensors=latest_ai_result.get("sensors", ["HTS221"]),
    )
    return {"profile": info, "ai_evaluation": latest_ai_result}


@app.post("/api/command/led")
def api_command_led(req: LedCommandRequest):
    allowed, note = copilot.guardrails.validate(
        "set_led", {"mode": req.mode, "force": req.force}, latest_ai_result
    )
    if not allowed:
        raise HTTPException(status_code=403, detail=note)
    cmd = publish_led_command(req.mode, req.r, req.g, req.b)
    return {"allowed": True, "note": note, "command": cmd}


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    executors = {
        "get_status": lambda p: latest_ai_result,
        "get_capa_report": lambda p: advisor.generate_report(latest_ai_result),
        "set_led": lambda p: publish_led_command(
            p.get("mode", "safe"), p.get("r", 0), p.get("g", 0), p.get("b", 0)
        ),
        "switch_profile": lambda p: api_set_profile(ProfileRequest(profile=p.get("profile", "coldchain"))),
        "simulate_crisis": lambda p: _execute_simulate(p.get("scenario", "normal")),
    }
    return copilot.process(req.message, latest_ai_result, executors)


@app.get("/api/audit")
def api_audit():
    return {"audit_log": copilot.audit_log}


@app.get("/api/mqtt-log")
def api_mqtt_log():
    return {"packets": list(mqtt_log)}


@app.get("/api/export.csv")
def api_export_csv(limit: int = 500):
    rows = get_history_records(min(limit, 5000))
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "timestamp_utc", "node_id", "temp_c", "humid_pct", "pressure_hpa", "vib_g", "shock", "risk_level", "health_score", "slope", "z_score", "scenario"])
    for r in rows:
        writer.writerow(r)
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=gmp_coldchain_audit_log.csv"},
    )


@app.post("/api/simulate-scenario")
def api_simulate(scenario: str = "normal"):
    return {"simulated": _execute_simulate(scenario)}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
