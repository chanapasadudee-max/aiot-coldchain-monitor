FROM python:3.12-slim

WORKDIR /app

# ติดตั้ง dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# คัดลอกโค้ดระบบ
COPY backend/ ./backend/
COPY ui/ ./ui/

WORKDIR /app/backend

EXPOSE 5000

ENV PORT=5000
ENV MQTT_HOST=broker.emqx.io
ENV MQTT_PORT=1883
ENV MQTT_TOPIC=tse/cn466/chanapa/telemetry

CMD ["python", "app.py"]
