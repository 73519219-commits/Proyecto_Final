from __future__ import annotations

import re
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import pyodbc

from app.core.config import settings

SCHEMA_FILE = Path(__file__).resolve().parents[2] / "sql" / "create_schema.sql"


def _odbc_value(value: str) -> str:
    return "{" + value.replace("}", "}}") + "}"


def connect(
    database: str | None = None,
    *,
    autocommit: bool = False,
) -> pyodbc.Connection:
    """Abre una conexión SQL Server usando autenticación integrada o SQL."""
    database_name = database or settings.database.name
    server = settings.database.host
    loopback_hosts = {"localhost", "127.0.0.1", ".", "(local)"}
    if settings.database.port and server.lower() not in loopback_hosts:
        server = f"{server},{settings.database.port}"
    parts = [
        f"DRIVER={_odbc_value(settings.database.driver)}",
        f"SERVER={_odbc_value(server)}",
        f"DATABASE={_odbc_value(database_name)}",
        f"Encrypt={'yes' if settings.database.encrypt else 'no'}",
        "TrustServerCertificate="
        f"{'yes' if settings.database.trust_server_certificate else 'no'}",
    ]

    if settings.database.trusted_connection:
        parts.append("Trusted_Connection=yes")
    else:
        parts.extend(
            (
                f"UID={_odbc_value(settings.database.user)}",
                f"PWD={_odbc_value(settings.database.password)}",
            )
        )

    return pyodbc.connect(
        ";".join(parts),
        timeout=settings.database.connection_timeout,
        autocommit=autocommit,
    )


def query_all(sql: str, *parameters: object) -> list[dict[str, object]]:
    with connection_scope() as connection:
        cursor = connection.cursor()
        cursor.execute(sql, *parameters)
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]


def query_one(sql: str, *parameters: object) -> dict[str, object] | None:
    with connection_scope() as connection:
        cursor = connection.cursor()
        cursor.execute(sql, *parameters)
        row = cursor.fetchone()
        if row is None:
            return None
        columns = [description[0] for description in cursor.description]
        return dict(zip(columns, row, strict=True))


def execute(sql: str, *parameters: object) -> int:
    with connection_scope() as connection:
        cursor = connection.cursor()
        cursor.execute(sql, *parameters)
        return cursor.rowcount


@contextmanager
def connection_scope(database: str | None = None) -> Iterator[pyodbc.Connection]:
    """Confirma operaciones correctas, revierte errores y siempre cierra la conexión."""
    connection = connect(database)
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database() -> None:
    """Crea la base de datos y su esquema, y carga los datos de demostración."""
    database_name = settings.database.name
    if not re.fullmatch(r"[A-Za-z0-9_]+", database_name):
        raise ValueError("DB_NAME solo puede contener letras, números y guiones bajos.")

    connection = connect("master", autocommit=True)
    try:
        cursor = connection.cursor()
        cursor.execute(
            "IF DB_ID(?) IS NULL EXEC(N'CREATE DATABASE "
            f"[{database_name}]');",
            database_name,
        )
    finally:
        connection.close()

    schema = SCHEMA_FILE.read_text(encoding="utf-8-sig")
    with connection_scope() as connection:
        cursor = connection.cursor()
        cursor.execute(schema)
        while cursor.nextset():
            pass

    faltantes = query_all(
        """
        SELECT esperado.nombre
        FROM (VALUES
            (N'usuarios'), (N'donaciones'), (N'solicitudes'),
            (N'entregas'), (N'rechazos_mision'), (N'avisos')
        ) AS esperado(nombre)
        WHERE OBJECT_ID(N'dbo.' + esperado.nombre, N'U') IS NULL
        """
    )
    if faltantes:
        nombres = ", ".join(str(tabla["nombre"]) for tabla in faltantes)
        raise RuntimeError(f"El esquema SQL no creó las tablas requeridas: {nombres}.")

    from app.data.demo_data import seed_demo_data

    seed_demo_data()
