"""
AIoT Industrial Cold Chain & Sensitive Facility Simulator (Multi-Sensor Edition)
File: sim_industrial.py
Author: Chanapa Sadudee (6610680214)

จำลองบอร์ด Cucumber RIS (ESP32-S2) ครบทุกเซ็นเซอร์:
  - HTS221: Temperature (°C), Humidity (%RH)
  - BMP280: Barometric Pressure (hPa)
  - MPU6050: Vibration Peak (G), Shock Detection
"""

import argparse
import json
import random
import sys
import time
from datetime import datetime, timezone
import paho.mqtt.client as mqtt

BROKER_DEFAULT = "broker.emqx.io"
PORT_DEFAULT = 1883
TOPIC_DEFAULT = "tse/cn466/chanapa/telemetry"

SCENARIOS = {
    "normal": "สภาวะปกติ (ตู้แช่ยา 2°C - 6°C)",
    "server": "สภาวะปกติ (ห้อง Server 19°C - 23°C)",
    "failure": "วิกฤต: คอมเพรสเซอร์เสีย (อุณหภูมิไต่ระดับขึ้นเร็วผิดปกติ)",
    "door_ajar": "วิกฤต: ลืมปิดประตูตู้แช่ (อุณหภูมิ/ความชื้นพุ่ง + ความดันเปลี่ยน)",
    "door_slam": "วิกฤต: แรงกระแทก/เปิดประตูแรง (MPU6050 Shock > 0.35g)",
    "glitch": "สไปก์ชั่วขณะ (Sensor Glitch จากคลื่นรบกวน)",
}


def parse_args():
    parser = argparse.ArgumentParser(description="AIoT Industrial Multi-Sensor Simulator")
    parser.add_argument("--host", default=BROKER_DEFAULT, help="MQTT Broker Host")
    parser.add_argument("--port", type=int, default=PORT_DEFAULT, help="MQTT Broker Port")
    parser.add_argument("--topic", default=TOPIC_DEFAULT, help="MQTT Topic")
    parser.add_argument("--interval", type=float, default=2.0, help="Publish interval in seconds")
    parser.add_argument("--scenario", default="normal", choices=list(SCENARIOS.keys()), help="Scenario mode")
    parser.add_argument("--node-id", default="cucumber-sim-01", help="Node ID")
    return parser.parse_args()


def main():
    args = parse_args()
    print("=" * 68)
    print(" AIoT Industrial Cold Chain Multi-Sensor Simulator")
    print(f" Target: {args.host}:{args.port} | Topic: {args.topic}")
    print(f" Scenario: {args.scenario} -> {SCENARIOS[args.scenario]}")
    print("=" * 68)

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    try:
        client.connect(args.host, args.port, keepalive=60)
        client.loop_start()
        print(f"[OK] Connected to MQTT Broker. Publishing every {args.interval}s...")
    except Exception as e:
        print(f"[ERR] MQTT connect failed: {e}")
        sys.exit(1)

    if args.scenario == "server":
        temp, humid, pressure = 21.0, 45.0, 1011.5
    else:
        temp, humid, pressure = 4.2, 61.0, 1012.8

    step = 0
    scenario = args.scenario

    try:
        while True:
            step += 1
            now_iso = datetime.now(timezone.utc).isoformat()
            vib_g = round(random.uniform(0.01, 0.05), 3)
            shock = False

            if scenario == "normal":
                temp = max(3.0, min(5.5, temp + random.uniform(-0.15, 0.15)))
                humid = max(55.0, min(68.0, humid + random.uniform(-0.5, 0.5)))
                pressure = max(1010.0, min(1015.0, pressure + random.uniform(-0.1, 0.1)))
            elif scenario == "server":
                temp = max(19.0, min(23.5, temp + random.uniform(-0.2, 0.2)))
                humid = max(40.0, min(50.0, humid + random.uniform(-0.4, 0.4)))
                pressure = max(1009.0, min(1014.0, pressure + random.uniform(-0.1, 0.1)))
            elif scenario == "failure":
                temp += random.uniform(0.30, 0.55)
                humid += random.uniform(0.2, 0.8)
                vib_g = round(random.uniform(0.12, 0.28), 3)
            elif scenario == "door_ajar":
                temp += random.uniform(0.20, 0.45)
                humid += random.uniform(0.8, 1.8)
                pressure -= random.uniform(0.2, 0.5)
            elif scenario == "door_slam":
                temp += random.uniform(0.10, 0.25)
                humid += random.uniform(0.4, 1.0)
                if step % 3 == 0:
                    vib_g = round(random.uniform(0.65, 1.45), 3)
                    shock = True
            elif scenario == "glitch":
                if step % 5 == 0:
                    temp = 14.8
                else:
                    temp = 4.1 + random.uniform(-0.1, 0.1)

            payload = {
                "node_id": args.node_id,
                "ts": now_iso,
                "step": step,
                "temp": round(temp, 2),
                "humid": round(humid, 2),
                "pressure": round(pressure, 2),
                "vib_g": vib_g,
                "shock": shock,
                "sensors": ["HTS221", "BMP280", "MPU6050"],
                "scenario": scenario,
            }

            client.publish(args.topic, json.dumps(payload))
            status = "SAFE" if temp <= 8.0 and not shock else "ALERT"
            print(
                f"[{step:03d}] {status:5} | Temp:{temp:5.2f}C | Humid:{humid:5.2f}% | "
                f"Press:{pressure:7.2f}hPa | Vib:{vib_g:.3f}g | Shock:{shock}"
            )
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n[STOP] Simulator stopped.")
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
