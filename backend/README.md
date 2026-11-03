# Backend de AlimentoSolidario Huancayo

Este proyecto contiene el backend académico de AlimentoSolidario Huancayo desarrollado con FastAPI, Pydantic y Python.

## Objetivo
- Exponer APIs REST para usuarios, donaciones, solicitudes y entregas.
- Trabajar con datos temporales en memoria, sin base de datos.
- Preparar la estructura para integrar una base de datos más adelante.

## Estructura

- `app/apis`: routers y endpoints REST.
- `app/schemas`: validaciones con Pydantic.
- `app/services`: lógica de negocio.
- `app/repositories`: acceso a datos en memoria.
- `app/data`: almacenamiento temporal.
- `app/core`: seguridad y JWT.

## Requisitos
- Python 3.14+
- uv

## Instalación

```bash
cd backend
uv sync
```

## Ejecutar servidor

```bash
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

o

```bash
uv run python main.py
```

## Documentación Swagger

- http://127.0.0.1:8000/docs
- http://127.0.0.1:8000/redoc

## Nota importante
Los datos se mantienen en memoria y se pierden cuando se reinicia el servidor. Esto es intencional para la fase académica del proyecto.
