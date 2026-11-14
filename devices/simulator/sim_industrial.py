"""
AIoT Industrial Cold Chain & Sensitive Facility Simulator
File: sim_industrial.py
Author: Chanapa Sadudee (6610680214)

โปรแกรมจำลองอุปกรณ์ IoT ประจำตู้แช่ยา/วัคซีน และห้อง Server ระดับอุตสาหกรรม
ส่งข้อมูล Telemetry ทาง MQTT พร้อมรองรับการจำลองวิกฤตความเย็น (Crisis Scenarios)
เพื่อให้ AI Engine และระบบแจ้งเตือน Telegram แสดงประสิทธิภาพในการตรวจจับ
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
    "door_ajar": "วิกฤต: ลืมปิดประตูตู้แช่ (อุณหภูมิและความชื้นพุ่งสูง)",
    "glitch": "สไปก์ชั่วขณะ (Sensor Glitch จากคลื่นรบกวน)",
}

def parse_args():
    parser = argparse.ArgumentParser(description="AIoT Industrial Sensor Simulator")
    parser.add_argument("--host", default=BROKER_DEFAULT, help="MQTT Broker Host")
    parser.add_argument("--port", type=int, default=PORT_DEFAULT, help="MQTT Broker Port")
    parser.add_argument("--topic", default=TOPIC_DEFAULT, help="MQTT Topic")
    parser.add_argument("--interval", type=float, default=2.0, help="Publish interval in seconds")
    parser.add_argument("--scenario", default="normal", choices=list(SCENARIOS.keys()), help="Scenario mode")
    parser.add_argument("--node-id", default="cucumber-coldchain-01", help="Node ID")
    return parser.parse_args()

def main():
    args = parse_args()
    print("=" * 65)
    print(" 🏭 AIoT Industrial Cold Chain Simulator")
    print(f" Target: {args.host}:{args.port} | Topic: {args.topic}")
    print(f" Scenario: {args.scenario} -> {SCENARIOS[args.scenario]}")
    print("=" * 65)

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    try:
        client.connect(args.host, args.port, keepalive=60)
        client.loop_start()
        print(f"✅ เชื่อมต่อ MQTT Broker สำเร็จ! เริ่มส่งข้อมูลทุกๆ {args.interval} วินาที...")
    except Exception as e:
        print(f"❌ เชื่อมต่อ MQTT ล้มเหลว: {e}")
        sys.exit(1)

    # กำหนดค่าเริ่มต้นตามสถานการณ์
    if args.scenario == "server":
        temp = 21.0
        humid = 45.0
    else:
        temp = 4.2
        humid = 62.0

    step = 0
    scenario = args.scenario

    try:
        while True:
            step += 1
            now_iso = datetime.now(timezone.utc).isoformat()

            # คำนวณค่าตามสถานการณ์
            if scenario == "normal":
                temp += random.uniform(-0.15, 0.15)
                temp = max(3.0, min(5.5, temp))
                humid += random.uniform(-0.5, 0.5)
                humid = max(55.0, min(68.0, humid))
            elif scenario == "server":
                temp += random.uniform(-0.2, 0.2)
                temp = max(19.0, min(23.5, temp))
                humid += random.uniform(-0.4, 0.4)
                humid = max(40.0, min(50.0, humid))
            elif scenario == "failure":
                # คอมเพรสเซอร์หยุดทำงาน อุณหภูมิไต่ขึ้นเร็วต่อเนื่อง
                temp += random.uniform(0.3, 0.6)
                humid += random.uniform(0.2, 0.8)
            elif scenario == "door_ajar":
                # ลืมปิดประตู ความร้อนชื้นภายนอกไหลเข้า
                temp += random.uniform(0.2, 0.45)
                humid += random.uniform(0.8, 1.8)
            elif scenario == "glitch":
                if step % 5 == 0:
                    temp = 14.8  # ค่าเด้งผิดปกติ 1 รอบ
                else:
                    temp = 4.1 + random.uniform(-0.1, 0.1)

            payload = {
                "node_id": args.node_id,
                "ts": now_iso,
                "step": step,
                "temp": round(temp, 2),
                "humid": round(humid, 2),
                "scenario": scenario
            }

            json_str = json.dumps(payload)
            client.publish(args.topic, json_str)
            
            # สัญลักษณ์บอกสถานะบนคอนโซล
            status_icon = "🟢" if temp <= 8.0 else ("🟡" if temp <= 10.0 else "🔴 ALERT")
            print(f"[{step:03d}] {status_icon} Temp: {temp:5.2f} °C | Humid: {humid:5.2f} % | {scenario} ({args.topic})")

            time.sleep(args.interval)

    except KeyboardInterrupt:
        print("\n⏹️ หยุดการทำงานของ Simulator...")
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()
