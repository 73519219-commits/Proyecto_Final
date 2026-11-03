from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.apis.donaciones import router as donaciones_router
from app.apis.solicitudes import router as solicitudes_router
from app.apis.usuarios import router as usuarios_router
from app.apis.voluntarios import router as voluntarios_router
from app.data.memoria import reset_demo_data

reset_demo_data()

app = FastAPI(
    title="AlimentoSolidario Huancayo API",
    description="Backend académico con FastAPI para gestión de donaciones, solicitudes y entregas.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(usuarios_router)
app.include_router(donaciones_router)
app.include_router(solicitudes_router)
app.include_router(voluntarios_router)

