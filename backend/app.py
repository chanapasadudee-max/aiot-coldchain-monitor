"""
AIoT Industrial Cold Chain Backend Service
File: app.py
Author: Chanapa Sadudee (6610680214)

บริการ Backend หลัก:
  - เชื่อมต่อ MQTT Broker (broker.emqx.io) หัวข้อ tse/cn466/chanapa/telemetry
  - จัดเก็บข้อมูลลงฐานข้อมูล SQLite (coldchain.db)
  - ส่งผ่านข้อมูลเข้า AI Anomaly Detection Engine แบบ Real-time
  - เปิด REST API สำหรับ Web Dashboard และ Telegram Mini App
  - เสิร์ฟหน้าเว็บ UI (HTML/CSS/JS)
"""

import json
import os
import sqlite3
import threading
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

import paho.mqtt.client as mqtt
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from ai_engine import IndustrialAnomalyEngine
from incident_advisor import IncidentAdvisor

# ---------------- การตั้งค่าระบบ ----------------
MQTT_HOST = os.getenv("MQTT_HOST", "broker.emqx.io")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "tse/cn466/chanapa/telemetry")
DB_PATH = os.getenv("DB_PATH", str(Path(__file__).parent / "coldchain.db"))
PORT = int(os.getenv("PORT", "5000"))

BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR.parent / "ui" / "static"

# สร้างเอนจิน AI
ai_engine = IndustrialAnomalyEngine(window_size=15, safe_min=2.0, safe_max=8.0)
advisor = IncidentAdvisor()

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
           risk_level TEXT NOT NULL,
           slope REAL NOT NULL,
           z_score REAL NOT NULL,
           scenario TEXT
       )"""
)
conn.commit()

def save_telemetry(node_id: str, temp: float, humid: float, ai_res: dict, scenario: str = "normal"):
    with db_lock:
        conn.execute(
            """INSERT INTO telemetry (ts, node_id, temp, humid, risk_level, slope, z_score, scenario)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                datetime.now(timezone.utc).isoformat(),
                node_id,
                temp,
                humid,
                ai_res["risk_level"],
                ai_res["slope_per_step"],
                ai_res["z_score"],
                scenario
            ),
        )
        conn.commit()

def get_latest_record():
    with db_lock:
        row = conn.execute(
            """SELECT id, ts, node_id, temp, humid, risk_level, slope, z_score, scenario 
               FROM telemetry ORDER BY id DESC LIMIT 1"""
        ).fetchone()
    return row

def get_history_records(limit: int = 40):
    with db_lock:
        rows = conn.execute(
            """SELECT id, ts, node_id, temp, humid, risk_level, slope, z_score, scenario 
               FROM telemetry ORDER BY id DESC LIMIT ?""",
            (limit,),
        ).fetchall()
    return rows

# ---------------- MQTT Subscriber ----------------
mqtt_connected = threading.Event()
latest_ai_result = {
    "current_temp": 4.2,
    "current_humid": 60.0,
    "moving_mean": 4.2,
    "std_dev": 0.0,
    "z_score": 0.0,
    "slope_per_step": 0.0,
    "risk_level": "NORMAL",
    "anomaly_detected": False,
    "anomaly_reasons": [],
    "ettf_seconds": None,
    "safe_range": [2.0, 8.0]
}

def on_connect(client, userdata, flags, reason_code, properties=None):
    print(f"[MQTT] Connected successfully (rc={reason_code}). Subscribing to: {MQTT_TOPIC}")
    client.subscribe(MQTT_TOPIC)
    mqtt_connected.set()

def on_message(client, userdata, msg):
    global latest_ai_result
    try:
        data = json.loads(msg.payload.decode())
        node_id = str(data.get("node_id", "cucumber-01"))
        temp = float(data["temp"])
        humid = float(data["humid"])
        scenario = str(data.get("scenario", "live"))
    except Exception as e:
        # ข้ามข้อความที่ format ไม่ตรง
        return

    # วิเคราะห์ด้วย AI
    ai_res = ai_engine.feed(temp, humid)
    latest_ai_result = ai_res
    save_telemetry(node_id, temp, humid, ai_res, scenario)

    # พิมพ์ผลวิเคราะห์ออกคอนโซล
    if ai_res["risk_level"] != "NORMAL":
        print(f"⚠️ [AI ALERT] {ai_res['risk_level']} - Temp: {temp}°C, Slope: {ai_res['slope_per_step']:.2f}")

mqtt_client = None

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
    description="ระบบเฝ้าระวังตู้แช่ยาและห้อง Server อุตสาหกรรม ด้วย AIoT",
    version="1.0.0",
    lifespan=lifespan
)

# เปิด CORS สำหรับเข้าถึงข้ามโดเมน
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# เสิร์ฟ static files
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
def serve_dashboard():
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "AIoT Backend is running. Please check static/index.html"}

@app.get("/api/health")
def api_health():
    with db_lock:
        count = conn.execute("SELECT COUNT(*) FROM telemetry").fetchone()[0]
    return {
        "status": "online",
        "service": "AIoT Cold Chain Anomaly Service",
        "mqtt_broker": MQTT_HOST,
        "mqtt_topic": MQTT_TOPIC,
        "mqtt_connected": mqtt_connected.is_set(),
        "total_readings": count
    }

@app.get("/api/latest")
def api_latest():
    row = get_latest_record()
    if not row:
        return {
            "telemetry": None,
            "ai_evaluation": latest_ai_result
        }
    return {
        "telemetry": {
            "id": row[0],
            "ts": row[1],
            "node_id": row[2],
            "temp": row[3],
            "humid": row[4],
            "risk_level": row[5],
            "slope": row[6],
            "z_score": row[7],
            "scenario": row[8]
        },
        "ai_evaluation": latest_ai_result
    }

@app.get("/api/history")
def api_history(limit: int = 30):
    rows = get_history_records(min(limit, 100))
    # แปลงเป็นลิสต์ของดิกชันนารีเรียงจากเก่าไปใหม่สำหรับวาดกราฟ
    records = []
    for r in reversed(rows):
        records.append({
            "id": r[0],
            "ts": r[1],
            "node_id": r[2],
            "temp": r[3],
            "humid": r[4],
            "risk_level": r[5],
            "slope": r[6],
            "z_score": r[7],
            "scenario": r[8]
        })
    return records

@app.get("/api/incident-report")
def api_incident_report():
    report = advisor.generate_report(latest_ai_result)
    return report

@app.post("/api/simulate-scenario")
def api_simulate(scenario: str = "normal"):
    """สำหรับปุ่มจำลองสถานการณ์บน Web Dashboard"""
    import random
    if scenario == "failure":
        temp = 9.8
        humid = 74.0
    elif scenario == "warning":
        temp = 6.8
        humid = 68.0
    else:
        temp = round(random.uniform(3.8, 5.2), 2)
        humid = round(random.uniform(58.0, 64.0), 2)

    payload = {
        "node_id": "sim-button",
        "temp": temp,
        "humid": humid,
        "scenario": scenario
    }
    if mqtt_client and mqtt_connected.is_set():
        mqtt_client.publish(MQTT_TOPIC, json.dumps(payload))
    return {"simulated": payload}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
