from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.apis.donaciones import router as donaciones_router
from app.apis.health import router as health_router
from app.apis.solicitudes import router as solicitudes_router
from app.apis.usuarios import router as usuarios_router
from app.apis.voluntarios import router as voluntarios_router
from app.apis.dashboard import router as dashboard_router
from app.apis.entregas import router as entregas_router
from app.apis.avisos import router as avisos_router
from app.core.config import settings
from app.core.database import initialize_database


def validate_runtime_settings() -> None:
    loopback_hosts = {"127.0.0.1", "localhost", "::1"}
    if settings.api_host.lower() in loopback_hosts:
        return
    if (
        settings.secret_key == "alimento-solidario-secret-key-demo"
        or len(settings.secret_key.encode("utf-8")) < 32
    ):
        raise RuntimeError("Configura una SECRET_KEY aleatoria de al menos 32 bytes antes de exponer la API.")
    if settings.database.trust_server_certificate:
        raise RuntimeError(
            "DB_TRUST_SERVER_CERTIFICATE debe ser false para conexiones de base de datos no locales."
        )


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    validate_runtime_settings()
    initialize_database()
    yield


app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(usuarios_router)
app.include_router(donaciones_router)
app.include_router(solicitudes_router)
app.include_router(voluntarios_router)
app.include_router(dashboard_router)
app.include_router(entregas_router)
app.include_router(avisos_router)
app.include_router(health_router)

