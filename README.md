# 🌱 Greenhouse Monitor

Sistema de monitorización de invernadero simulado. Práctica de DevOps + IoT con Docker.

## Arquitectura

```
sensor-simulator → API (FastAPI) → InfluxDB → Grafana
```

| Servicio          | Puerto | Descripción                          |
|-------------------|--------|--------------------------------------|
| sensor-simulator  | —      | Genera datos cada 10s y los envía    |
| api               | 8000   | Recibe, valida y persiste los datos  |
| influxdb          | 8086   | Base de datos de series temporales   |
| grafana           | 3000   | Dashboard de visualización           |

## Inicio rápido

```bash
docker compose up --build
```

Después de ~20 segundos (InfluxDB tarda en arrancar):

- **Grafana** → http://localhost:3000  (admin / admin)
- **API docs** → http://localhost:8000/docs
- **InfluxDB UI** → http://localhost:8086 (admin / adminpassword)

El dashboard "Greenhouse Monitor" aparece automáticamente en Grafana
dentro de la carpeta "Greenhouse".

## Estructura del proyecto

```
greenhouse/
├── docker-compose.yml
├── api/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── main.py              # FastAPI + validación Pydantic
├── sensor-simulator/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── simulator.py         # Genera datos con ruido y drift senoidal
└── grafana/
    └── provisioning/
        ├── datasources/
        │   └── influxdb.yml # Conexión auto-configurada a InfluxDB
        └── dashboards/
            ├── dashboards.yml
            └── greenhouse.json  # Dashboard pre-configurado
```

## Sensores simulados

| Sensor     | Zona      | Temp base | Humedad base | Luz base |
|------------|-----------|-----------|--------------|----------|
| sensor-01  | Tomates   | 24 °C     | 65 %         | 8000 lux |
| sensor-02  | Setas     | 18 °C     | 85 %         | 500 lux  |

Los valores oscilan con un drift senoidal lento + ruido gaussiano para
que las gráficas parezcan datos reales.

## Validación de la API

Los datos se validan con Pydantic antes de escribir en InfluxDB:

| Campo       | Rango válido         |
|-------------|----------------------|
| temperature | −20 °C a 60 °C       |
| humidity    | 0 % a 100 %          |
| light       | 0 a 100 000 lux      |

Prueba manual con curl:

```bash
curl -X POST http://localhost:8000/sensors \
  -H "Content-Type: application/json" \
  -d '{"sensor_id":"manual-01","temperature":22.5,"humidity":70.0,"light":5000}'
```

## Parar el sistema

```bash
docker compose down          # para contenedores, conserva volúmenes
docker compose down -v       # para contenedores y borra datos
```

## Próximos pasos posibles

- [ ] Alertas en Grafana (ej: temperatura fuera de rango)
- [ ] Añadir MQTT como broker de mensajes
- [ ] Pipeline CI/CD con GitHub Actions
- [ ] Tests automáticos para la API
- [ ] Exportar métricas a Prometheus
- [ ] Migrar a Kubernetes (k3s / minikube)
