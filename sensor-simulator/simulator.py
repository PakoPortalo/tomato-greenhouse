"""
Greenhouse sensor simulator.

Generates realistic environmental readings for a small greenhouse and POSTs
them to the API every INTERVAL_SECONDS seconds.

Simulated sensors:
  - sensor-01  (zone A – tomatoes)
  - sensor-02  (zone B – mushrooms, darker & cooler)

Each reading adds small random noise on top of slowly-drifting base values so
Grafana graphs look natural rather than flat.
"""

import os
import math
import random
import time
import logging

import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

API_URL          = os.environ.get("API_URL", "http://localhost:8000/sensors")
INTERVAL_SECONDS = int(os.environ.get("INTERVAL_SECONDS", "10"))

# Sensor profiles: (temp_base, humidity_base, light_base)
SENSORS = {
    "sensor-01": {"temp": 24.0, "humidity": 65.0, "light": 8000.0},   # tomatoes
    "sensor-02": {"temp": 18.0, "humidity": 85.0, "light":  500.0},   # mushrooms
}


def sine_drift(t: float, period: float = 600, amplitude: float = 1.0) -> float:
    """Slow sinusoidal drift so values wander naturally over time."""
    return amplitude * math.sin(2 * math.pi * t / period)


def generate_reading(sensor_id: str, t: float) -> dict:
    base = SENSORS[sensor_id]

    temperature = (
        base["temp"]
        + sine_drift(t, period=600, amplitude=2.5)   # ±2.5 °C over 10 min
        + random.gauss(0, 0.3)                        # small noise
    )
    humidity = (
        base["humidity"]
        + sine_drift(t, period=900, amplitude=5.0)    # ±5 % over 15 min
        + random.gauss(0, 0.8)
    )
    # Light ramps up/down to simulate a day cycle (fast in simulation: 20-min period)
    light = (
        base["light"]
        + sine_drift(t, period=1200, amplitude=base["light"] * 0.4)
        + random.gauss(0, base["light"] * 0.03)
    )

    return {
        "sensor_id":   sensor_id,
        "temperature": round(max(-20, min(60,     temperature)), 2),
        "humidity":    round(max(0,   min(100,    humidity)),    2),
        "light":       round(max(0,   min(100000, light)),       2),
    }


def send_reading(payload: dict) -> bool:
    try:
        resp = requests.post(API_URL, json=payload, timeout=5)
        resp.raise_for_status()
        return True
    except requests.exceptions.ConnectionError:
        log.warning("API not reachable yet, will retry…")
    except requests.exceptions.HTTPError as exc:
        log.error("API returned error: %s – %s", exc.response.status_code, exc.response.text)
    except Exception as exc:
        log.error("Unexpected error: %s", exc)
    return False


def main():
    log.info("Sensor simulator starting (API: %s, interval: %ss)", API_URL, INTERVAL_SECONDS)
    # Wait for the API to become available
    while True:
        try:
            requests.get(API_URL.replace("/sensors", "/health"), timeout=3)
            log.info("API is reachable. Starting data generation…")
            break
        except Exception:
            log.info("Waiting for API…")
            time.sleep(3)

    t = 0.0
    while True:
        for sensor_id in SENSORS:
            payload = generate_reading(sensor_id, t)
            ok = send_reading(payload)
            if ok:
                log.info(
                    "[%s] temp=%.1f°C  humidity=%.1f%%  light=%.0f lux",
                    sensor_id,
                    payload["temperature"],
                    payload["humidity"],
                    payload["light"],
                )

        time.sleep(INTERVAL_SECONDS)
        t += INTERVAL_SECONDS


if __name__ == "__main__":
    main()
