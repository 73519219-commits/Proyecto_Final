"""Configuración centralizada del backend.

Todas las variables se leen del archivo ``backend/.env`` (si existe) y del
entorno del proceso.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)

DEFAULT_CORS_ORIGINS = "http://localhost:4200,http://127.0.0.1:4200"


def _env_list(name: str, default: str) -> list[str]:
    """Lee una variable separada por comas y devuelve una lista limpia."""
    raw_value = os.getenv(name, default)
    return [item.strip() for item in raw_value.split(",") if item.strip()]


def _env_int(name: str, default: str) -> int:
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return int(default)


@dataclass(frozen=True)
class DatabaseSettings:
    """Configuración para SQL Server."""

    host: str = field(default_factory=lambda: os.getenv("DB_HOST", "localhost"))
    port: int = field(default_factory=lambda: _env_int("DB_PORT", "1433"))
    name: str = field(default_factory=lambda: os.getenv("DB_NAME", "alimento_solidario"))
    user: str = field(default_factory=lambda: os.getenv("DB_USER", "sa"))
    password: str = field(default_factory=lambda: os.getenv("DB_PASSWORD", ""))
    driver: str = field(
        default_factory=lambda: os.getenv("DB_DRIVER", "ODBC Driver 18 for SQL Server")
    )
    trusted_connection: bool = field(
        default_factory=lambda: os.getenv("DB_TRUSTED_CONNECTION", "true").lower()
        in {"true", "1", "yes"}
    )
    encrypt: bool = field(
        default_factory=lambda: os.getenv("DB_ENCRYPT", "true").lower()
        in {"true", "1", "yes"}
    )
    trust_server_certificate: bool = field(
        default_factory=lambda: os.getenv(
            "DB_TRUST_SERVER_CERTIFICATE", "true"
        ).lower()
        in {"true", "1", "yes"}
    )
    connection_timeout: int = field(
        default_factory=lambda: _env_int("DB_CONNECTION_TIMEOUT", "5")
    )


@dataclass(frozen=True)
class Settings:
    app_name: str = field(
        default_factory=lambda: os.getenv("APP_NAME", "AlimentoSolidario Huancayo API")
    )
    app_description: str = field(
        default_factory=lambda: os.getenv(
            "APP_DESCRIPTION",
            "Backend académico con FastAPI para gestión de donaciones, solicitudes y entregas.",
        )
    )
    app_version: str = field(default_factory=lambda: os.getenv("APP_VERSION", "1.0.0"))
    api_host: str = field(default_factory=lambda: os.getenv("API_HOST", "127.0.0.1"))
    api_port: int = field(default_factory=lambda: _env_int("API_PORT", "8000"))
    cors_origins: list[str] = field(
        default_factory=lambda: _env_list("CORS_ORIGINS", DEFAULT_CORS_ORIGINS)
    )
    secret_key: str = field(
        default_factory=lambda: os.getenv("SECRET_KEY", "alimento-solidario-secret-key-demo")
    )
    access_token_expire_minutes: int = field(
        default_factory=lambda: _env_int("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")
    )
    database: DatabaseSettings = field(default_factory=DatabaseSettings)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
