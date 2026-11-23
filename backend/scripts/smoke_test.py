"""Prueba HTTP completa de la cadena de AlimentoSolidario.

Requiere FastAPI y SQL Server en ejecucion:
    uv run python -m scripts.smoke_test
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import date, timedelta
from typing import Any
from uuid import uuid4

from app.core.database import (
    connection_scope,
    initialize_database,
    query_all,
    query_one,
)


BASE_URL = os.getenv("ALIMENTO_API_BASE_URL", "http://127.0.0.1:8000")
USUARIOS = {
    "admin": ("admin@alimentosolidario.pe", "admin123"),
    "negocio": ("negocio@panaderia.pe", "negocio123"),
    "comedor": ("comedor@esperanza.pe", "comedor123"),
    "voluntario": ("voluntario@correo.pe", "voluntario123"),
}

tabla: list[tuple[str, str, str, bool]] = []


def peticion(
    metodo: str,
    ruta: str,
    token: str | None = None,
    cuerpo: dict[str, Any] | None = None,
) -> tuple[int, Any]:
    headers = {"Accept": "application/json"}
    datos = None
    if cuerpo is not None:
        headers["Content-Type"] = "application/json"
        datos = json.dumps(cuerpo).encode("utf-8")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    solicitud = urllib.request.Request(
        f"{BASE_URL}{ruta}",
        data=datos,
        headers=headers,
        method=metodo,
    )
    try:
        with urllib.request.urlopen(solicitud, timeout=10) as respuesta:
            texto = respuesta.read().decode("utf-8")
            return respuesta.status, json.loads(texto) if texto else None
    except urllib.error.HTTPError as error:
        texto = error.read().decode("utf-8")
        try:
            datos_error = json.loads(texto)
        except json.JSONDecodeError:
            datos_error = texto
        return error.code, datos_error


def afirmar(paso: str, esperado: str, obtenido: str, ok: bool) -> None:
    tabla.append((paso, esperado, obtenido, ok))


def login(rol: str) -> tuple[str, dict[str, Any]]:
    correo, password = USUARIOS[rol]
    status, datos = peticion(
        "POST",
        "/api/auth/login",
        cuerpo={"correo": correo, "password": password},
    )
    if status != 200:
        raise RuntimeError(f"Login fallido para {rol}: {status} {datos}")
    return datos["access_token"], datos["usuario"]


def buscar_por_id(datos: Any, entidad_id: int) -> dict[str, Any] | None:
    if not isinstance(datos, list):
        return None
    return next((item for item in datos if item.get("id") == entidad_id), None)


def main() -> int:
    initialize_database()
    donacion_id = 0
    solicitud_id = 0
    entrega_id = 0
    entregas_demo: list[dict[str, Any]] = []
    voluntario_disponible: bool | None = None
    usuario_temporal_id = 0

    try:
        correo_temporal = f"smoke_{uuid4().hex}@example.com"
        status, usuario_temporal = peticion(
            "POST",
            "/api/auth/registro",
            cuerpo={
                "nombres": "Prueba",
                "apellidos": "Temporal",
                "correo": correo_temporal,
                "password": "SmokeTest-123!",
                "telefono": "900000001",
                "direccion": "Dirección temporal de prueba",
                "rol": "voluntario",
            },
        )
        usuario_temporal_id = (
            int(usuario_temporal["id"]) if isinstance(usuario_temporal, dict) else 0
        )
        afirmar(
            "Registro de usuario",
            "201 con rol voluntario",
            f"{status} rol={usuario_temporal.get('rol') if isinstance(usuario_temporal, dict) else 'inválido'}",
            status == 201
            and isinstance(usuario_temporal, dict)
            and usuario_temporal.get("rol") == "voluntario",
        )
        status, login_temporal = peticion(
            "POST",
            "/api/auth/login",
            cuerpo={"correo": correo_temporal, "password": "SmokeTest-123!"},
        )
        afirmar(
            "Login de usuario registrado",
            "200 con token",
            f"{status} token={'presente' if isinstance(login_temporal, dict) and login_temporal.get('access_token') else 'ausente'}",
            status == 200
            and isinstance(login_temporal, dict)
            and bool(login_temporal.get("access_token")),
        )

        tokens: dict[str, str] = {}
        usuarios: dict[str, dict[str, Any]] = {}
        for rol in ("admin", "negocio", "comedor", "voluntario"):
            tokens[rol], usuarios[rol] = login(rol)

        status, avisos_legacy = peticion(
            "GET",
            "/api/voluntarios/avisos",
            token=tokens["voluntario"],
        )
        afirmar(
            "Ruta de avisos de voluntarios",
            "200 con lista",
            f"{status} registros={len(avisos_legacy) if isinstance(avisos_legacy, list) else 'inválido'}",
            status == 200 and isinstance(avisos_legacy, list),
        )

        estado_voluntario = query_one(
            "SELECT disponible FROM dbo.usuarios WHERE id = ?",
            usuarios["voluntario"]["id"],
        )
        if estado_voluntario is None:
            raise RuntimeError("No se encontró el voluntario de demostración.")
        voluntario_disponible = bool(estado_voluntario["disponible"])

        # Aísla el voluntario demo de misiones aceptadas o recogidas previas.
        entregas_demo = query_all(
            """
            SELECT id, voluntario_id, fecha_asignacion, fecha_entrega,
                   estado, observaciones, tipo_apoyo, tipo
            FROM dbo.entregas
            WHERE voluntario_id = ?
            """,
            usuarios["voluntario"]["id"],
        )
        with connection_scope() as connection:
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE dbo.usuarios SET disponible = 1 WHERE id = ?",
                usuarios["voluntario"]["id"],
            )
            cursor.execute(
                """
                UPDATE dbo.entregas
                SET estado = N'cancelada', voluntario_id = NULL
                WHERE voluntario_id = ? AND estado IN (N'abierta', N'aceptada', N'recogida')
                """,
                usuarios["voluntario"]["id"],
            )

        status, disponible = peticion(
            "PATCH",
            "/api/usuarios/me/disponible?disponible=true",
            token=tokens["voluntario"],
        )
        afirmar(
            "Voluntario disponible",
            "200 disponible=true",
            f"{status} disponible={disponible.get('disponible') if isinstance(disponible, dict) else disponible}",
            status == 200
            and isinstance(disponible, dict)
            and disponible.get("disponible") is True,
        )

        # Negocio publica.
        payload_donacion = {
            "nombre_alimento": "Producto humo completo",
            "descripcion": "Donacion temporal para prueba HTTP.",
            "cantidad": 30,
            "unidad": "kg",
            "fecha_vencimiento": (date.today() + timedelta(days=30)).isoformat(),
            "direccion_recojo": "Av. Prueba Humo 123",
            "hora_disponible": "09:00 - 12:00",
            "estado": "disponible",
            "usuario_negocio_id": usuarios["negocio"]["id"],
        }
        status, donacion = peticion(
            "POST", "/api/donaciones/", tokens["negocio"], payload_donacion
        )
        donacion_id = donacion["id"] if isinstance(donacion, dict) else 0
        afirmar(
            "1 Negocio publica",
            "201 y estado disponible",
            f"{status} estado={donacion.get('estado') if isinstance(donacion, dict) else donacion}",
            status == 201
            and isinstance(donacion, dict)
            and donacion.get("estado") == "disponible",
        )

        # Comedor solicita.
        status, solicitud = peticion(
            "POST",
            "/api/solicitudes/",
            tokens["comedor"],
            {
                "donacion_id": donacion_id,
                "comedor_id": usuarios["comedor"]["id"],
                "cantidad_solicitada": 5,
                "tipo_apoyo": "ambos",
                "necesita_apoyo": "recoger",
                "estado": "pendiente",
            },
        )
        solicitud_id = solicitud["id"] if isinstance(solicitud, dict) else 0
        afirmar(
            "2 Comedor solicita",
            "201 pendiente",
            f"{status} estado={solicitud.get('estado') if isinstance(solicitud, dict) else solicitud}",
            status == 201
            and isinstance(solicitud, dict)
            and solicitud.get("estado") == "pendiente",
        )

        # Antes de aprobar no se debe serializar telefono.
        _, solicitudes_comedor = peticion("GET", "/api/solicitudes/", tokens["comedor"])
        actual = buscar_por_id(solicitudes_comedor, solicitud_id)
        telefono_oculto = (
            actual is not None
            and actual.get("telefono_negocio") is None
            and actual.get("telefono_comedor") is None
        )
        afirmar(
            "Telefono antes de aprobar",
            "telefono_negocio=null telefono_comedor=null",
            f"{actual.get('telefono_negocio') if actual else 'n/a'} / "
            f"{actual.get('telefono_comedor') if actual else 'n/a'}",
            telefono_oculto,
        )

        # Aviso de solicitud creada y rol cruzado prohibido.
        _, avisos_negocio = peticion("GET", "/api/avisos/", tokens["negocio"])
        aviso_creada = isinstance(avisos_negocio, list) and any(
            item.get("tipo") == "solicitud_creada"
            and item.get("referencia_id") == solicitud_id
            for item in avisos_negocio
        )
        afirmar(
            "Aviso solicitud creada",
            "tipo=solicitud_creada al negocio",
            "presente" if aviso_creada else "ausente",
            aviso_creada,
        )

        status, _ = peticion(
            "POST",
            f"/api/solicitudes/{solicitud_id}/aprobar",
            tokens["comedor"],
            {"tipo_apoyo": "recoger"},
        )
        afirmar(
            "403 rol cruzado aprobar",
            "403 comedor no aprueba",
            str(status),
            status == 403,
        )

        # Negocio aprueba y ajusta apoyo.
        status, aprobada = peticion(
            "POST",
            f"/api/solicitudes/{solicitud_id}/aprobar",
            tokens["negocio"],
            {"tipo_apoyo": "recoger"},
        )
        afirmar(
            "3 Negocio aprueba",
            "200 aprobada",
            f"{status} estado={aprobada.get('estado') if isinstance(aprobada, dict) else aprobada}",
            status == 200
            and isinstance(aprobada, dict)
            and aprobada.get("estado") == "aprobada",
        )

        _, solicitudes_negocio = peticion("GET", "/api/solicitudes/", tokens["negocio"])
        actual_negocio = buscar_por_id(solicitudes_negocio, solicitud_id)
        telefono_visible = (
            actual_negocio is not None
            and bool(actual_negocio.get("telefono_negocio"))
            and bool(actual_negocio.get("telefono_comedor"))
        )
        afirmar(
            "Telefono despues aprobar",
            "ambos telefonos visibles al dueño",
            "visible" if telefono_visible else "oculto",
            telefono_visible,
        )

        _, avisos_comedor = peticion("GET", "/api/avisos/", tokens["comedor"])
        aviso_aprobada = isinstance(avisos_comedor, list) and any(
            item.get("tipo") == "solicitud_aprobada"
            and item.get("referencia_id") == solicitud_id
            for item in avisos_comedor
        )
        afirmar(
            "Aviso solicitud aprobada",
            "tipo=solicitud_aprobada al comedor",
            "presente" if aviso_aprobada else "ausente",
            aviso_aprobada,
        )

        # Obtiene la entrega creada.
        _, entregas = peticion("GET", "/api/entregas/abiertas", tokens["voluntario"])
        entrega = buscar_por_id(entregas, solicitud_id)
        if entrega is None and isinstance(entregas, list):
            # La lista abierta usa id de entrega, no id de solicitud.
            entrega = next(
                (item for item in entregas if item.get("solicitud_id") == solicitud_id),
                None,
            )
        entrega_id = entrega["id"] if isinstance(entrega, dict) else 0
        afirmar(
            "Entrega creada abierta",
            "estado=abierta",
            f"entrega={entrega_id} estado={entrega.get('estado') if isinstance(entrega, dict) else 'n/a'}",
            isinstance(entrega, dict) and entrega.get("estado") == "abierta",
        )

        # Voluntario acepta.
        status, aceptada = peticion(
            "POST",
            f"/api/voluntarios/entregas/{entrega_id}/aceptar",
            tokens["voluntario"],
        )
        afirmar(
            "4 Voluntario acepta",
            "200 aceptada",
            f"{status} estado={aceptada.get('estado') if isinstance(aceptada, dict) else aceptada}",
            status == 200
            and isinstance(aceptada, dict)
            and aceptada.get("estado") == "aceptada",
        )

        _, avisos_comedor = peticion("GET", "/api/avisos/", tokens["comedor"])
        aviso_aceptada = isinstance(avisos_comedor, list) and any(
            item.get("tipo") == "mision_aceptada"
            and item.get("referencia_id") == entrega_id
            for item in avisos_comedor
        )
        afirmar(
            "Aviso misión aceptada",
            "tipo=mision_aceptada al comedor",
            "presente" if aviso_aceptada else "ausente",
            aviso_aceptada,
        )

        status, recogida = peticion(
            "POST",
            f"/api/voluntarios/entregas/{entrega_id}/recogido",
            tokens["voluntario"],
        )
        afirmar(
            "5 Voluntario recogido",
            "200 recogida",
            f"{status} estado={recogida.get('estado') if isinstance(recogida, dict) else recogida}",
            status == 200
            and isinstance(recogida, dict)
            and recogida.get("estado") == "recogida",
        )

        _, avisos_comedor = peticion("GET", "/api/avisos/", tokens["comedor"])
        aviso_recogida_comedor = isinstance(avisos_comedor, list) and any(
            item.get("tipo") == "entrega_recogida"
            and item.get("referencia_id") == entrega_id
            for item in avisos_comedor
        )
        _, avisos_negocio = peticion("GET", "/api/avisos/", tokens["negocio"])
        aviso_recogida_negocio = isinstance(avisos_negocio, list) and any(
            item.get("tipo") == "entrega_recogida"
            and item.get("referencia_id") == entrega_id
            for item in avisos_negocio
        )
        afirmar(
            "Avisos recogida",
            "entrega_recogida en comedor y negocio",
            f"comedor={aviso_recogida_comedor} negocio={aviso_recogida_negocio}",
            aviso_recogida_comedor and aviso_recogida_negocio,
        )

        status, entregada = peticion(
            "POST",
            f"/api/voluntarios/entregas/{entrega_id}/confirmar",
            tokens["comedor"],
        )
        afirmar(
            "6 Comedor confirma",
            "200 entregada",
            f"{status} estado={entregada.get('estado') if isinstance(entregada, dict) else entregada}",
            status == 200
            and isinstance(entregada, dict)
            and entregada.get("estado") == "entregada",
        )

        _, avisos_comedor = peticion("GET", "/api/avisos/", tokens["comedor"])
        aviso_entregada = isinstance(avisos_comedor, list) and any(
            item.get("tipo") == "entrega_entregada"
            and item.get("referencia_id") == entrega_id
            for item in avisos_comedor
        )
        afirmar(
            "Aviso entregada",
            "entrega_entregada al comedor",
            "presente" if aviso_entregada else "ausente",
            aviso_entregada,
        )

        # Contadores distintos por rol y nunca usuarios a no-admin.
        contadores: dict[str, dict[str, Any]] = {}
        for rol in ("negocio", "comedor", "voluntario", "admin"):
            status, datos = peticion("GET", "/api/dashboard/resumen", tokens[rol])
            contadores[rol] = datos if status == 200 and isinstance(datos, dict) else {}
        claves = {rol: tuple(sorted(datos.keys())) for rol, datos in contadores.items()}
        distintos = len(set(claves["negocio"]) if contadores else []) >= 1
        distintos = distintos and (
            claves["negocio"] != claves["comedor"]
            and claves["comedor"] != claves["voluntario"]
            and claves["voluntario"] != claves["admin"]
        )
        sin_usuarios = all(
            "usuarios" not in key and "total_usuarios" not in key
            for rol in ("negocio", "comedor", "voluntario")
            for key in claves[rol]
        )
        afirmar(
            "Contadores por rol",
            "negocio/comedor/voluntario/admin distintos; no-admin sin usuarios",
            json.dumps(claves, ensure_ascii=False),
            distintos and sin_usuarios,
        )

        # El trabajo no se intercambia entre roles.
        status, _ = peticion(
            "POST",
            f"/api/solicitudes/{solicitud_id}/rechazar",
            tokens["voluntario"],
        )
        afirmar(
            "403 voluntario rechaza solicitud",
            "403",
            str(status),
            status == 403,
        )
        status, _ = peticion(
            "POST",
            f"/api/voluntarios/entregas/{entrega_id}/aceptar",
            tokens["negocio"],
        )
        afirmar(
            "403 negocio acepta misión",
            "403",
            str(status),
            status == 403,
        )

        print("Paso | Esperado | Obtenido")
        print("--- | --- | ---")
        for paso, esperado, obtenido, ok in tabla:
            print(f"{paso} | {esperado} | {'OK: ' if ok else 'FALLO: '}{obtenido}")
        fallos = [item for item in tabla if not item[3]]
        print()
        print(f"Total: {len(tabla)} | Correctos: {len(tabla)-len(fallos)} | Fallos: {len(fallos)}")
        return 1 if fallos else 0
    except Exception as error:
        print("Paso | Esperado | Obtenido")
        print("--- | --- | ---")
        for paso, esperado, obtenido, ok in tabla:
            print(f"{paso} | {esperado} | {'OK: ' if ok else 'FALLO: '}{obtenido}")
        print(f"ERROR: {error}")
        return 1
    finally:
        with connection_scope() as connection:
            cursor = connection.cursor()
            if donacion_id:
                cursor.execute(
                    "SELECT id FROM dbo.solicitudes WHERE donacion_id = ?",
                    donacion_id,
                )
                solicitudes_temporales = [int(fila[0]) for fila in cursor.fetchall()]
                for id_solicitud in solicitudes_temporales:
                    cursor.execute(
                        "SELECT id FROM dbo.entregas WHERE solicitud_id = ?",
                        id_solicitud,
                    )
                    entregas_temporales = [int(fila[0]) for fila in cursor.fetchall()]
                    for id_entrega in entregas_temporales:
                        cursor.execute(
                            "DELETE FROM dbo.avisos WHERE referencia_id = ?",
                            id_entrega,
                        )
                        cursor.execute(
                            "DELETE FROM dbo.rechazos_mision WHERE entrega_id = ?",
                            id_entrega,
                        )
                        cursor.execute(
                            "DELETE FROM dbo.entregas WHERE id = ?",
                            id_entrega,
                        )
                    cursor.execute(
                        "DELETE FROM dbo.avisos WHERE referencia_id = ?",
                        id_solicitud,
                    )
                    cursor.execute(
                        "DELETE FROM dbo.solicitudes WHERE id = ?",
                        id_solicitud,
                    )
                cursor.execute("DELETE FROM dbo.donaciones WHERE id = ?", donacion_id)
            for entrega_demo in entregas_demo:
                cursor.execute(
                    """
                    UPDATE dbo.entregas
                    SET voluntario_id = ?, fecha_asignacion = ?, fecha_entrega = ?,
                        estado = ?, observaciones = ?, tipo_apoyo = ?, tipo = ?
                    WHERE id = ?
                    """,
                    entrega_demo["voluntario_id"],
                    entrega_demo["fecha_asignacion"],
                    entrega_demo["fecha_entrega"],
                    entrega_demo["estado"],
                    entrega_demo["observaciones"],
                    entrega_demo["tipo_apoyo"],
                    entrega_demo["tipo"],
                    entrega_demo["id"],
                )
            if voluntario_disponible is not None:
                cursor.execute(
                    "UPDATE dbo.usuarios SET disponible = ? WHERE correo = ?",
                    voluntario_disponible,
                    USUARIOS["voluntario"][0],
                )
            if usuario_temporal_id:
                cursor.execute(
                    "DELETE FROM dbo.usuarios WHERE id = ?",
                    usuario_temporal_id,
                )


if __name__ == "__main__":
    raise SystemExit(main())
