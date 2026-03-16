import os
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# --- Config ---
INFLUXDB_URL    = os.environ["INFLUXDB_URL"]
INFLUXDB_TOKEN  = os.environ["INFLUXDB_TOKEN"]
INFLUXDB_ORG    = os.environ["INFLUXDB_ORG"]
INFLUXDB_BUCKET = os.environ["INFLUXDB_BUCKET"]

# --- InfluxDB client ---
client    = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
write_api = client.write_api(write_options=SYNCHRONOUS)

# --- FastAPI app ---
app = FastAPI(title="Greenhouse Sensor API", version="1.0.0")


# --- Data model with validation ---
class SensorReading(BaseModel):
    sensor_id: str = Field(..., min_length=1, max_length=50)
    temperature: float = Field(..., ge=-20.0, le=60.0,
                               description="Temperature in °C, range -20 to 60")
    humidity: float    = Field(..., ge=0.0, le=100.0,
                               description="Relative humidity %, range 0 to 100")

# --- Endpoints ---
@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/sensors", status_code=201)
def receive_sensor_data(reading: SensorReading):
    """Receive a sensor reading and persist it to InfluxDB."""
    try:
        point = (
            Point("environment")
            .tag("sensor_id", reading.sensor_id)
            .field("temperature", reading.temperature)
            .field("humidity",    reading.humidity)
            .time(datetime.now(timezone.utc), WritePrecision.S)        )
        write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"InfluxDB write error: {exc}")

    return {
        "status":    "recorded",
        "sensor_id": reading.sensor_id,
        "data": {
            "temperature": reading.temperature,
            "humidity":    reading.humidity,
        },
    }
