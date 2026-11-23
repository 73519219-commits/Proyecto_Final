from __future__ import annotations

from dataclasses import replace
from typing import Any

import pytest
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.apis.donaciones import router as donaciones_router
from app.apis.usuarios import router as usuarios_router
from app.apis.solicitudes import router as solicitudes_router
from app.apis.voluntarios import router as voluntarios_router
from app.apis.dashboard import router as dashboard_router
from app.apis.entregas import router as entregas_router
from app.apis.avisos import router as avisos_router
from app.core.seguridad import get_current_user
from app.repositories.donacion_repository import DonacionRepository, DonacionRevisionError
from app.repositories.solicitud_repository import (
    SolicitudRepository,
    SolicitudRevisionError,
)
from app.repositories.usuario_repository import UsuarioCorreoDuplicado, UsuarioRepository
from app.services.donacion_service import DonacionService
from app.services.solicitud_service import SolicitudService
from app.services.usuario_service import UsuarioService
from app.repositories.dashboard_repository import DashboardRepository
from app.repositories.entrega_repository import EntregaRepository
from app.services.voluntario_service import VoluntarioService
from app.schemas.solicitud import SolicitudCreate, SolicitudUpdate
from app.schemas.donacion import DonacionCreate
from app.schemas.usuario import UsuarioCreate
from app.services.aviso_service import AvisoService
from app.repositories.aviso_repository import AvisoRepository
from app.main import validate_runtime_settings
from app.core.config import settings


USUARIO_ADMIN = {"id": 1, "rol": "admin", "estado": "activo"}
USUARIO_NEGOCIO = {"id": 2, "rol": "negocio", "estado": "activo"}
USUARIO_COMEDOR = {"id": 3, "rol": "comedor", "estado": "activo"}


def crear_cliente(usuario: dict[str, Any] | None = None) -> TestClient:
    aplicacion = FastAPI()
    aplicacion.include_router(usuarios_router)
    aplicacion.include_router(donaciones_router)
    aplicacion.include_router(solicitudes_router)
    aplicacion.include_router(voluntarios_router)
    aplicacion.include_router(dashboard_router)
    aplicacion.include_router(entregas_router)
    aplicacion.include_router(avisos_router)
    aplicacion.dependency_overrides[get_current_user] = lambda: usuario or USUARIO_ADMIN
    return TestClient(aplicacion)


def donacion() -> dict[str, Any]:
    return {
        "id": 11,
        "nombre_alimento": "Pan de trigo",
        "descripcion": "Pan en buen estado para donar.",
        "cantidad": 20,
        "unidad": "unidad",
        "fecha_vencimiento": "2027-01-30",
        "direccion_recojo": "Av. Real 320",
        "hora_disponible": "08:00 - 10:00",
        "estado": "disponible",
        "usuario_negocio_id": 2,
    }


def test_login_emite_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        UsuarioService,
        "autenticar",
        lambda datos: {
            "id": 1,
            "correo": datos.correo,
            "rol": "admin",
            "estado": "activo",
            "nombres": "Admin",
            "apellidos": "Demo",
            "telefono": "987654321",
            "direccion": "Jr. Puno 120",
        },
    )
    cliente = crear_cliente()

    respuesta = cliente.post(
        "/api/auth/login",
        json={"correo": "admin@alimentosolidario.pe", "password": "admin123"},
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["token_type"] == "bearer"
    assert respuesta.json()["access_token"]


def test_registro_publico_rechaza_admin_y_openapi_lo_excluye(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        UsuarioService,
        "registrar_usuario",
        lambda _: pytest.fail("No debe registrar un administrador"),
    )
    cliente = crear_cliente()
    payload = {
        "nombres": "Admin",
        "apellidos": "No autorizado",
        "correo": "admin.nuevo@example.com",
        "password": "password123",
        "telefono": "987654321",
        "direccion": "Jr. Prueba 100",
        "rol": "admin",
    }

    respuesta = cliente.post("/api/auth/registro", json=payload)
    schema = cliente.get("/openapi.json").json()["components"]["schemas"]
    roles_registrables = schema["UsuarioCreate"]["properties"]["rol"]["enum"]

    assert respuesta.status_code == 422
    assert set(roles_registrables) == {"negocio", "comedor", "voluntario"}


def test_crud_donaciones(monkeypatch: pytest.MonkeyPatch) -> None:
    registro = donacion()
    monkeypatch.setattr(DonacionService, "listar_donaciones", lambda: [registro])
    monkeypatch.setattr(DonacionService, "registrar_donacion", lambda _: registro)
    monkeypatch.setattr(DonacionService, "buscar_por_id", lambda _id: registro)
    monkeypatch.setattr(
        DonacionService,
        "actualizar_donacion",
        lambda _id, datos: {**registro, **datos.model_dump(exclude_unset=True)},
    )
    monkeypatch.setattr(
        DonacionService,
        "eliminar_donacion",
        lambda _id: {"mensaje": "Donación cancelada correctamente."},
    )
    cliente = crear_cliente(USUARIO_NEGOCIO)
    payload = {key: value for key, value in registro.items() if key != "id"}

    assert cliente.get("/api/donaciones/").json() == [registro]
    assert cliente.post("/api/donaciones/", json=payload).status_code == 201
    respuesta_actualizar = cliente.put(
        "/api/donaciones/11", json={"cantidad": 15}
    )
    assert respuesta_actualizar.status_code == 200
    assert respuesta_actualizar.json()["cantidad"] == 15
    respuesta_borrar = cliente.delete("/api/donaciones/11")
    assert respuesta_borrar.status_code == 200
    assert "cancelada" in respuesta_borrar.json()["mensaje"].lower()


def test_usuario_no_autorizado_recibe_403(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        DonacionService,
        "registrar_donacion",
        lambda _: pytest.fail("No debe llamar al servicio"),
    )
    respuesta = crear_cliente(USUARIO_COMEDOR).post(
        "/api/donaciones/", json={key: value for key, value in donacion().items() if key != "id"}
    )

    assert respuesta.status_code == 403


def test_admin_puede_listar_todas_las_solicitudes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    solicitudes = [{
        "id": 11,
        "donacion_id": 20,
        "comedor_id": 3,
        "cantidad_solicitada": 5,
        "tipo_apoyo": "ambos",
        "necesita_apoyo": "ambos",
        "estado": "pendiente",
        "usuario_negocio_id": 2,
    }]
    monkeypatch.setattr(SolicitudService, "listar_solicitudes", lambda: solicitudes)

    respuesta = crear_cliente(USUARIO_ADMIN).get("/api/solicitudes/")

    assert respuesta.status_code == 200
    assert respuesta.json()[0]["id"] == 11


@pytest.mark.parametrize("estado", ["aprobada", "rechazada"])
def test_solicitud_no_se_puede_crear_con_estado_de_revision(
    estado: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        SolicitudService,
        "registrar_solicitud",
        lambda _: pytest.fail("No debe registrar una solicitud ya revisada"),
    )
    payload = {
        "donacion_id": 20,
        "comedor_id": USUARIO_COMEDOR["id"],
        "cantidad_solicitada": 2,
        "estado": estado,
    }

    respuesta = crear_cliente(USUARIO_COMEDOR).post(
        "/api/solicitudes/",
        json=payload,
    )

    assert respuesta.status_code == 422


@pytest.mark.parametrize(
    ("usuario", "estado"),
    [
        (USUARIO_COMEDOR, "aprobada"),
        (USUARIO_COMEDOR, "rechazada"),
        (USUARIO_ADMIN, "aprobada"),
        (USUARIO_ADMIN, "rechazada"),
    ],
)
def test_put_no_puede_aprobar_ni_rechazar_solicitud(
    usuario: dict[str, Any],
    estado: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        SolicitudService,
        "buscar_por_id",
        lambda _id: {"id": 11, "comedor_id": USUARIO_COMEDOR["id"]},
    )
    monkeypatch.setattr(
        SolicitudService,
        "actualizar_solicitud",
        lambda *_args: pytest.fail("La actualización no debe ejecutarse"),
    )

    respuesta = crear_cliente(usuario).put(
        "/api/solicitudes/11",
        json={"estado": estado},
    )

    assert respuesta.status_code == 403


@pytest.mark.parametrize("metodo", ["put", "patch", "delete"])
def test_edicion_y_baja_de_usuario_requieren_admin(metodo: str) -> None:
    cliente = crear_cliente(USUARIO_COMEDOR)
    if metodo == "delete":
        respuesta = cliente.delete("/api/usuarios/5")
    else:
        respuesta = getattr(cliente, metodo)(
            "/api/usuarios/5", json={"direccion": "Jr. Prueba 100"}
        )

    assert respuesta.status_code == 403


@pytest.mark.parametrize(
    ("usuario_id", "campo", "valor"),
    [
        (3, "rol", "admin"),
        (3, "estado", "inactivo"),
        (5, "rol", "admin"),
        (5, "estado", "inactivo"),
    ],
)
def test_no_admin_no_puede_cambiar_rol_ni_estado(
    usuario_id: int,
    campo: str,
    valor: str,
) -> None:
    respuesta = crear_cliente(USUARIO_COMEDOR).patch(
        f"/api/usuarios/{usuario_id}", json={campo: valor}
    )

    assert respuesta.status_code == 403


def test_filtro_de_rol_usa_parametro_sql(monkeypatch: pytest.MonkeyPatch) -> None:
    consultas: list[tuple[str, tuple[object, ...]]] = []

    def capturar(consulta: str, *parametros: object) -> list[dict[str, Any]]:
        consultas.append((consulta, parametros))
        return []

    monkeypatch.setattr("app.repositories.usuario_repository.query_all", capturar)
    inyeccion = "voluntario' OR '1'='1"

    UsuarioRepository.listar(inyeccion)

    assert len(consultas) == 1
    consulta, parametros = consultas[0]
    assert "WHERE rol = ?" in consulta
    assert inyeccion not in consulta
    assert parametros == (inyeccion,)


@pytest.mark.parametrize(
    ("servicio", "repositorio", "estado"),
    [
        (DonacionService, DonacionRepository, "cancelada"),
        (SolicitudService, SolicitudRepository, "cancelada"),
    ],
)
def test_no_permite_cancelacion_duplicada(
    monkeypatch: pytest.MonkeyPatch,
    servicio: Any,
    repositorio: Any,
    estado: str,
) -> None:
    monkeypatch.setattr(
        repositorio,
        "buscar_por_id",
        lambda _id: {"id": 11, "estado": estado},
    )
    monkeypatch.setattr(
        repositorio,
        "cancelar_atomica",
        lambda _id: pytest.fail("No debe repetir la baja lógica"),
    )

    if servicio is DonacionService:
        monkeypatch.setattr(
            repositorio,
            "cancelar_atomica",
            lambda _id: (_ for _ in ()).throw(DonacionRevisionError(409, "Donación ya cancelada.")),
        )
        llamada = lambda: servicio.eliminar_donacion(11)
    else:
        llamada = lambda: servicio.cancelar_solicitud(11)

    with pytest.raises(HTTPException) as error:
        llamada()

    assert error.value.status_code == 409


def test_solo_negocio_aprueba_solicitud(monkeypatch: pytest.MonkeyPatch) -> None:
    solicitud = {
        "id": 11,
        "donacion_id": 20,
        "comedor_id": 3,
        "cantidad_solicitada": 5,
        "tipo_apoyo": "ambos",
        "estado": "pendiente",
    }
    monkeypatch.setattr(SolicitudService, "aprobar", lambda *_args: {**solicitud, "estado": "aprobada"})
    cliente = crear_cliente(USUARIO_COMEDOR)

    respuesta = cliente.post("/api/solicitudes/11/aprobar", json={"tipo_apoyo": "recoger"})

    assert respuesta.status_code == 403


def test_negocio_aprueba_solicitud_con_tipo_apoyo(monkeypatch: pytest.MonkeyPatch) -> None:
    solicitado = {
        "id": 11,
        "donacion_id": 20,
        "comedor_id": 3,
        "cantidad_solicitada": 5,
        "tipo_apoyo": "recoger",
        "estado": "aprobada",
    }
    monkeypatch.setattr(
        SolicitudService,
        "aprobar",
        lambda _id, _negocio, tipo: {**solicitado, "tipo_apoyo": tipo},
    )
    respuesta = crear_cliente(USUARIO_NEGOCIO).post(
        "/api/solicitudes/11/aprobar",
        json={"tipo_apoyo": "recoger"},
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "aprobada"
    assert respuesta.json()["tipo_apoyo"] == "recoger"


@pytest.mark.parametrize(
    ("usuario", "esperado"),
    [
        (USUARIO_NEGOCIO, {"publicaciones_activas": 2}),
        (USUARIO_COMEDOR, {"disponibles_ahora": 4}),
        ({"id": 4, "rol": "voluntario", "estado": "activo", "disponible": True}, {"misiones_abiertas": 1}),
    ],
)
def test_dashboard_resumen_es_distinto_por_rol(
    monkeypatch: pytest.MonkeyPatch,
    usuario: dict[str, Any],
    esperado: dict[str, int],
) -> None:
    monkeypatch.setattr(
        DashboardRepository,
        "resumen",
        lambda actual: (
            {"publicaciones_activas": 2} if actual["rol"] == "negocio"
            else {"disponibles_ahora": 4} if actual["rol"] == "comedor"
            else {"misiones_abiertas": 1}
        ),
    )
    respuesta = crear_cliente(usuario).get("/api/dashboard/resumen")

    assert respuesta.status_code == 200
    assert respuesta.json() == esperado


def test_entregas_abiertas_filtran_pasadas_por_parametro(monkeypatch: pytest.MonkeyPatch) -> None:
    consultas: list[tuple[str, tuple[object, ...]]] = []

    def capturar(consulta: str, *parametros: object) -> list[dict[str, Any]]:
        consultas.append((consulta, parametros))
        return []

    monkeypatch.setattr("app.repositories.entrega_repository.query_all", capturar)
    usuario = {"id": 4, "rol": "voluntario", "estado": "activo", "disponible": True}

    EntregaRepository.listar_abiertas(usuario["id"])

    assert len(consultas) == 1
    consulta, parametros = consultas[0]
    assert "r.voluntario_id = ?" in consulta
    assert parametros == (4,)


@pytest.mark.parametrize(
    ("estado_actual", "estado_nuevo", "valida"),
    [
        ("abierta", "aceptada", False),
        ("aceptada", "recogida", True),
        ("recogida", "entregada", True),
        ("abierta", "cancelada", True),
        ("aceptada", "cancelada", True),
        ("recogida", "cancelada", True),
        ("abierta", "recogida", False),
        ("entregada", "aceptada", False),
        ("entregada", "cancelada", False),
        ("cancelada", "cancelada", False),
    ],
)
def test_transiciones_entrega(
    monkeypatch: pytest.MonkeyPatch,
    estado_actual: str,
    estado_nuevo: str,
    valida: bool,
) -> None:
    entrega = {"id": 9, "estado": estado_actual, "solicitud_id": 3}
    monkeypatch.setattr(EntregaRepository, "buscar_por_id", lambda _id: entrega)
    monkeypatch.setattr(
        SolicitudRepository,
        "buscar_por_id",
        lambda _id: {"id": 3, "comedor_id": 3, "donacion_id": 20, "estado": "aprobada"},
    )
    monkeypatch.setattr(
        DonacionRepository,
        "buscar_por_id",
        lambda _id: {"id": 20, "usuario_negocio_id": 2},
    )
    from app.services.aviso_service import AvisoService
    avisos: list[tuple] = []
    monkeypatch.setattr(AvisoService, "crear", lambda *args: avisos.append(args))
    def cambiar_entrega(_id: int, _actual: str, nuevo: str) -> None:
        entrega["estado"] = nuevo

    monkeypatch.setattr(EntregaRepository, "cambiar_estado_atomico", cambiar_entrega)
    monkeypatch.setattr(
        SolicitudRepository,
        "cancelar_atomica",
        lambda _id: entrega.update(estado="cancelada"),
    )

    if valida:
        resultado = VoluntarioService.cambiar_estado_controlado(9, estado_nuevo)
        assert resultado["estado"] == estado_nuevo
        if estado_nuevo == "recogida":
            assert {aviso[0] for aviso in avisos} == {2, 3}
        if estado_nuevo == "entregada":
            assert {aviso[0] for aviso in avisos} == {3}
    else:
        with pytest.raises(HTTPException) as error:
            VoluntarioService.cambiar_estado_controlado(9, estado_nuevo)
        assert error.value.status_code == 409


@pytest.mark.parametrize(
    ("usuario", "voluntario_id", "esperado"),
    [
        (USUARIO_ADMIN, 4, 200),
        ({"id": 4, "rol": "voluntario", "estado": "activo"}, 4, 200),
        ({"id": 5, "rol": "voluntario", "estado": "activo"}, 4, 403),
    ],
)
def test_cancelar_entrega_requiere_admin_o_voluntario_asignado(
    usuario: dict[str, Any],
    voluntario_id: int,
    esperado: int,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entrega = {
        "id": 12,
        "solicitud_id": 11,
        "voluntario_id": voluntario_id,
        "fecha_asignacion": "2026-11-22",
        "fecha_entrega": None,
        "estado": "aceptada",
        "observaciones": None,
        "tipo_apoyo": "ambos",
        "tipo": "ambos",
    }
    monkeypatch.setattr(VoluntarioService, "obtener_entrega", lambda _id: entrega)
    monkeypatch.setattr(
        VoluntarioService,
        "actualizar_estado",
        lambda _id, estado: {**entrega, "estado": estado},
    )

    respuesta = crear_cliente(usuario).patch(
        "/api/voluntarios/entregas/12/estado",
        json={"estado": "cancelada"},
    )

    assert respuesta.status_code == esperado
    if esperado == 200:
        assert respuesta.json()["estado"] == "cancelada"


@pytest.mark.parametrize(
    ("usuario", "metodo", "ids_esperados"),
    [
        (USUARIO_ADMIN, "todas", [1, 2]),
        (USUARIO_COMEDOR, "comedor", [1]),
        (USUARIO_NEGOCIO, "negocio", [2]),
        (
            {"id": 4, "rol": "voluntario", "estado": "activo", "disponible": True},
            "voluntario",
            [1],
        ),
    ],
)
def test_entregas_abiertas_se_filtran_por_participante(
    usuario: dict[str, Any],
    metodo: str,
    ids_esperados: list[int],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    filas = [
        {"id": 1, "estado": "abierta", "comedor_id": 3, "usuario_negocio_id": 2, "voluntario_id": 0},
        {"id": 2, "estado": "abierta", "comedor_id": 5, "usuario_negocio_id": 6, "voluntario_id": 0},
    ]
    llamadas: list[tuple[str, int | None]] = []
    monkeypatch.setattr(
        EntregaRepository,
        "listar_abiertas_para",
        lambda voluntario_id: llamadas.append(("todas", voluntario_id)) or filas,
    )
    monkeypatch.setattr(
        EntregaRepository,
        "listar_abiertas_para_comedor",
        lambda comedor_id: llamadas.append(("comedor", comedor_id)) or [filas[0]],
    )
    monkeypatch.setattr(
        EntregaRepository,
        "listar_abiertas_para_negocio",
        lambda negocio_id: llamadas.append(("negocio", negocio_id)) or [filas[1]],
    )
    monkeypatch.setattr(
        EntregaRepository,
        "listar_abiertas",
        lambda voluntario_id: llamadas.append(("voluntario", voluntario_id)) or [filas[0]],
    )

    respuesta = crear_cliente(usuario).get("/api/entregas/abiertas")

    assert respuesta.status_code == 200
    assert [entrega["id"] for entrega in respuesta.json()] == ids_esperados
    assert llamadas == [(metodo, None if metodo == "todas" else usuario["id"])]


@pytest.mark.parametrize(
    ("metodo", "identificador", "filtro"),
    [
        ("listar_abiertas_para_comedor", 3, "s.comedor_id = ?"),
        ("listar_abiertas_para_negocio", 2, "d.usuario_negocio_id = ?"),
    ],
)
def test_filtro_de_entregas_abiertas_usa_parametros_sql(
    metodo: str,
    identificador: int,
    filtro: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    consultas: list[tuple[str, tuple[object, ...]]] = []

    def capturar(consulta: str, *parametros: object) -> list[dict[str, Any]]:
        consultas.append((consulta, parametros))
        return []

    monkeypatch.setattr("app.repositories.entrega_repository.query_all", capturar)

    getattr(EntregaRepository, metodo)(identificador)

    assert len(consultas) == 1
    consulta, parametros = consultas[0]
    assert "e.estado = N'abierta'" in consulta
    assert filtro in consulta
    assert parametros == (identificador,)


def test_comedor_no_ve_solicitudes_ajenas(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        SolicitudService,
        "listar_por_comedor",
        lambda comedor_id: [{
            "id": 1,
            "donacion_id": 11,
            "comedor_id": comedor_id,
            "cantidad_solicitada": 5,
            "tipo_apoyo": "ambos",
            "necesita_apoyo": "ambos",
            "estado": "pendiente",
        }],
    )
    cliente = crear_cliente(USUARIO_COMEDOR)

    respuesta = cliente.get("/api/solicitudes/")

    assert respuesta.status_code == 200
    assert all(item["comedor_id"] == USUARIO_COMEDOR["id"] for item in respuesta.json())


def test_negocio_no_aprueba_solicitud_ajena(monkeypatch: pytest.MonkeyPatch) -> None:
    solicitud = {
        "id": 11,
        "donacion_id": 20,
        "comedor_id": 3,
        "cantidad_solicitada": 5,
        "estado": "pendiente",
    }
    monkeypatch.setattr(SolicitudRepository, "buscar_por_id", lambda _id: solicitud)
    monkeypatch.setattr(
        DonacionRepository,
        "buscar_por_id",
        lambda _id: {"id": 20, "usuario_negocio_id": 99, "estado": "disponible"},
    )

    with pytest.raises(HTTPException) as error:
        SolicitudService.aprobar(11, USUARIO_NEGOCIO["id"], "ambos")

    assert error.value.status_code == 403


def test_solicitud_creada_genera_aviso_al_negocio(monkeypatch: pytest.MonkeyPatch) -> None:
    datos = SolicitudCreate(
        donacion_id=20,
        comedor_id=3,
        cantidad_solicitada=5,
        necesita_apoyo="ambos",
    )
    creada = {"id": 11, "donacion_id": 20, "comedor_id": 3, "cantidad_solicitada": 5, "estado": "pendiente"}
    monkeypatch.setattr(DonacionRepository, "buscar_por_id", lambda _id: {"id": 20, "estado": "disponible", "cantidad": 10, "fecha_vencimiento": "2099-01-01", "usuario_negocio_id": 2})
    monkeypatch.setattr(SolicitudRepository, "crear", lambda _datos: creada)
    avisos: list[tuple] = []
    monkeypatch.setattr(AvisoService, "crear", lambda *args: avisos.append(args))

    resultado = SolicitudService.registrar_solicitud(datos)

    assert resultado["id"] == 11
    assert avisos == [(2, "solicitud_creada", "Un comedor creó una solicitud sobre tu donación.", 11)]


@pytest.mark.parametrize(("estado", "tipo"), [("aprobada", "solicitud_aprobada"), ("rechazada", "solicitud_rechazada")])
def test_revision_solicitud_avisa_solo_comedor(monkeypatch: pytest.MonkeyPatch, estado: str, tipo: str) -> None:
    solicitud = {"id": 11, "donacion_id": 20, "comedor_id": 3, "estado": "pendiente"}
    solicitud_actual = dict(solicitud)
    monkeypatch.setattr(SolicitudRepository, "buscar_por_id", lambda _id: solicitud_actual)
    monkeypatch.setattr(DonacionRepository, "buscar_por_id", lambda _id: {"id": 20, "usuario_negocio_id": 2, "estado": "disponible"})
    monkeypatch.setattr(SolicitudRepository, "actualizar", lambda _id, datos: {**solicitud, **datos})
    monkeypatch.setattr(
        SolicitudRepository,
        "aprobar_atomica",
        lambda *_args: solicitud_actual.update(estado="aprobada"),
    )
    monkeypatch.setattr(
        SolicitudRepository,
        "rechazar_atomica",
        lambda *_args: solicitud_actual.update(estado="rechazada"),
    )
    avisos: list[tuple] = []
    monkeypatch.setattr(AvisoService, "crear", lambda *args: avisos.append(args))

    if estado == "aprobada":
        SolicitudService.aprobar(11, 2, "ambos")
    else:
        SolicitudService.rechazar(11, 2)

    assert any(aviso[0] == 3 and aviso[1] == tipo for aviso in avisos)
    assert all(aviso[0] == 3 for aviso in avisos)


def test_aprobacion_rechaza_cantidad_total_excedida(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    solicitud = {
        "id": 11,
        "donacion_id": 20,
        "comedor_id": 3,
        "cantidad_solicitada": 8,
        "tipo_apoyo": "ambos",
        "necesita_apoyo": "ambos",
        "estado": "pendiente",
    }
    monkeypatch.setattr(SolicitudRepository, "buscar_por_id", lambda _id: solicitud)
    monkeypatch.setattr(
        DonacionRepository,
        "buscar_por_id",
        lambda _id: {
            "id": 20,
            "cantidad": 10,
            "usuario_negocio_id": 2,
            "estado": "disponible",
        },
    )

    def excedida(*_args: object) -> None:
        raise SolicitudRevisionError(
            400,
            "La suma aprobada supera la cantidad disponible de la donación.",
        )

    monkeypatch.setattr(SolicitudRepository, "aprobar_atomica", excedida)

    with pytest.raises(HTTPException) as error:
        SolicitudService.aprobar(11, 2, "ambos")

    assert error.value.status_code == 400
    assert "cantidad disponible" in error.value.detail


@pytest.mark.parametrize(
    ("estado_donacion", "fecha_vencimiento", "status_esperado"),
    [
        ("cancelada", "2099-01-01", 409),
        ("disponible", "2000-01-01", 400),
    ],
)
def test_aprobacion_rechaza_donacion_no_disponible_o_vencida(
    monkeypatch: pytest.MonkeyPatch,
    estado_donacion: str,
    fecha_vencimiento: str,
    status_esperado: int,
) -> None:
    solicitud = {
        "id": 11,
        "donacion_id": 20,
        "comedor_id": 3,
        "cantidad_solicitada": 5,
        "estado": "pendiente",
    }
    monkeypatch.setattr(SolicitudRepository, "buscar_por_id", lambda _id: solicitud)
    monkeypatch.setattr(
        DonacionRepository,
        "buscar_por_id",
        lambda _id: {
            "id": 20,
            "cantidad": 10,
            "usuario_negocio_id": 2,
            "estado": estado_donacion,
            "fecha_vencimiento": fecha_vencimiento,
        },
    )

    with pytest.raises(HTTPException) as error:
        SolicitudService.aprobar(11, 2, "ambos")

    assert error.value.status_code == status_esperado


def test_cancelacion_rechaza_entrega_completada(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    solicitud = {"id": 11, "estado": "aprobada", "comedor_id": 3}
    monkeypatch.setattr(SolicitudRepository, "buscar_por_id", lambda _id: solicitud)

    def completada(*_args: object) -> None:
        raise SolicitudRevisionError(
            409,
            "No se puede cancelar una solicitud cuya entrega fue completada.",
        )

    monkeypatch.setattr(SolicitudRepository, "cancelar_atomica", completada)

    with pytest.raises(HTTPException) as error:
        SolicitudService.cancelar_solicitud(11)

    assert error.value.status_code == 409
    assert "entrega fue completada" in error.value.detail


def test_cancelacion_aprobada_libera_solicitud_atomica(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    solicitud = {"id": 11, "estado": "aprobada", "comedor_id": 3}
    monkeypatch.setattr(SolicitudRepository, "buscar_por_id", lambda _id: solicitud)
    llamada: list[int] = []
    monkeypatch.setattr(
        SolicitudRepository,
        "cancelar_atomica",
        lambda solicitud_id: llamada.append(solicitud_id),
    )

    resultado = SolicitudService.cancelar_solicitud(11)

    assert llamada == [11]
    assert "correctamente" in resultado["mensaje"]


def test_solicitud_aprobada_no_admite_edicion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        SolicitudRepository,
        "buscar_por_id",
        lambda _id: {"id": 11, "estado": "aprobada"},
    )
    monkeypatch.setattr(
        SolicitudRepository,
        "actualizar",
        lambda *_args: pytest.fail("No debe editarse una solicitud aprobada"),
    )

    with pytest.raises(HTTPException) as error:
        SolicitudService.actualizar_solicitud(
            11,
            SolicitudUpdate(cantidad_solicitada=4),
        )

    assert error.value.status_code == 409


def test_esquema_impide_entregas_duplicadas_por_solicitud() -> None:
    schema = (
        Path(__file__).resolve().parents[1] / "sql" / "create_schema.sql"
    ).read_text(encoding="utf-8-sig")

    assert "UQ_entregas_solicitud" in schema
    assert "CREATE UNIQUE INDEX UQ_entregas_solicitud" in schema
    assert "CREATE UNIQUE INDEX UQ_entregas_voluntario_activo" in schema
    assert "ON dbo.entregas (voluntario_id)" in schema
    assert "IF OBJECT_ID(N'dbo.avisos', N'U') IS NULL" in schema
    assert "IF OBJECT_ID(N'dbo.rechazos_mision', N'U') IS NULL" in schema
    assert "ALTER TABLE dbo.entregas ADD voluntario_activo_id" not in schema
    assert "HAVING COUNT(*) > 1" in schema


def test_telefono_oculto_pendiente_y_para_usuario_no_relacionado() -> None:
    solicitudes = [{
        "id": 11,
        "donacion_id": 20,
        "comedor_id": 3,
        "usuario_negocio_id": 2,
        "cantidad_solicitada": 5,
        "estado": "pendiente",
        "telefono_negocio": "961",
        "telefono_comedor": "991",
    }]

    resultado = SolicitudService.filtrar_telefonos(solicitudes, USUARIO_COMEDOR)

    assert resultado[0]["telefono_negocio"] is None
    assert resultado[0]["telefono_comedor"] is None

    aprobada = [{**solicitudes[0], "estado": "aprobada"}]
    resultado_comedor_ajeno = SolicitudService.filtrar_telefonos(aprobada, {"id": 99, "rol": "comedor"})
    assert resultado_comedor_ajeno[0]["telefono_negocio"] is None
    assert resultado_comedor_ajeno[0]["telefono_comedor"] is None

    resultado_negocio = SolicitudService.filtrar_telefonos(aprobada, USUARIO_NEGOCIO)
    assert resultado_negocio[0]["telefono_negocio"] == "961"
    assert resultado_negocio[0]["telefono_comedor"] == "991"


def test_mision_aceptada_avisa_comedor_y_negocio_recogida(monkeypatch: pytest.MonkeyPatch) -> None:
    entrega = {"id": 12, "estado": "abierta", "solicitud_id": 11, "tipo_apoyo": "recoger", "voluntario_id": 0}
    monkeypatch.setattr(EntregaRepository, "buscar_por_id", lambda _id: entrega)
    monkeypatch.setattr(EntregaRepository, "aceptar_atomica", lambda _id, _voluntario: entrega.update(estado="aceptada"))
    monkeypatch.setattr(SolicitudRepository, "buscar_por_id", lambda _id: {"id": 11, "comedor_id": 3, "donacion_id": 20, "estado": "aprobada"})
    monkeypatch.setattr(DonacionRepository, "buscar_por_id", lambda _id: {"id": 20, "usuario_negocio_id": 2})
    avisos: list[tuple] = []
    monkeypatch.setattr(AvisoService, "crear", lambda *args: avisos.append(args))

    VoluntarioService.aceptar_entrega(12, 4)

    assert {aviso[0] for aviso in avisos} == {2, 3}
    assert all(aviso[1] == "mision_aceptada" for aviso in avisos)


def test_voluntario_actualiza_solo_su_disponibilidad(monkeypatch: pytest.MonkeyPatch) -> None:
    usuario = {
        "id": 4,
        "nombres": "Carlos",
        "apellidos": "Ruiz",
        "correo": "voluntario@correo.pe",
        "telefono": "965432100",
        "direccion": "Urb. San Martín",
        "rol": "voluntario",
        "disponible": True,
        "estado": "activo",
    }
    monkeypatch.setattr(UsuarioService, "actualizar_usuario", lambda id_usuario, datos: {**usuario, "disponible": datos.disponible})

    respuesta = crear_cliente({"id": 4, "rol": "voluntario", "estado": "activo", "disponible": False}).patch(
        "/api/usuarios/me/disponible",
        params={"disponible": "true"},
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["disponible"] is True


def test_avisos_endpoints_solo_propios(monkeypatch: pytest.MonkeyPatch) -> None:
    aviso = {
        "id": 1,
        "usuario_destino": 3,
        "tipo": "solicitud_aprobada",
        "mensaje": "Aprobada",
        "referencia_id": 11,
        "leido": False,
        "created_at": "2026-11-21T14:00:00",
    }
    monkeypatch.setattr(AvisoService, "listar", lambda usuario_id: [aviso] if usuario_id == 3 else [])
    monkeypatch.setattr(AvisoService, "marcar_leido", lambda aviso_id, usuario_id: {**aviso, "leido": True} if usuario_id == 3 else None)

    cliente = crear_cliente(USUARIO_COMEDOR)
    listado = cliente.get("/api/avisos/")
    marcado = cliente.patch("/api/avisos/1/leer")

    assert listado.status_code == 200
    assert listado.json()[0]["usuario_destino"] == 3
    assert marcado.status_code == 200
    assert marcado.json()["leido"] is True


def test_password_respeta_limite_bcrypt_en_bytes() -> None:
    datos = {
        "nombres": "Ana",
        "apellidos": "Pérez",
        "correo": "ana@example.com",
        "telefono": "123456",
        "direccion": "Calle de prueba",
        "rol": "voluntario",
    }

    UsuarioCreate(**datos, password="🙂" * 18)
    with pytest.raises(ValidationError):
        UsuarioCreate(**datos, password="🙂" * 19)


def test_correo_duplicado_entre_consulta_e_insercion_es_conflicto_http(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    datos = UsuarioCreate(
        nombres="Ana",
        apellidos="Pérez",
        correo="ana@example.com",
        telefono="123456",
        direccion="Calle de prueba",
        rol="voluntario",
        password="segura123",
    )
    monkeypatch.setattr(UsuarioRepository, "buscar_por_correo", lambda _correo: None)

    def duplicar(_usuario: dict[str, Any]) -> dict[str, Any]:
        raise UsuarioCorreoDuplicado

    monkeypatch.setattr(UsuarioRepository, "crear", duplicar)
    with pytest.raises(HTTPException) as error:
        UsuarioService.registrar_usuario(datos)

    assert error.value.status_code == 409


def test_donacion_rechaza_nombre_mayor_que_columna_sql() -> None:
    datos = {
        "nombre_alimento": "A" * 151,
        "descripcion": "Alimento en buen estado",
        "cantidad": 1,
        "unidad": "kg",
        "fecha_vencimiento": "2099-01-01",
        "direccion_recojo": "Dirección de prueba",
        "hora_disponible": "09:00 - 10:00",
        "usuario_negocio_id": 2,
    }

    with pytest.raises(ValidationError):
        DonacionCreate(**datos)


def test_donacion_requiere_negocio_activo(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    datos = DonacionCreate(
        nombre_alimento="Pan",
        descripcion="Pan fresco para donar",
        cantidad=2,
        unidad="kg",
        fecha_vencimiento="2099-01-01",
        direccion_recojo="Calle de prueba",
        hora_disponible="09:00 - 10:00",
        usuario_negocio_id=3,
    )
    monkeypatch.setattr(
        UsuarioRepository,
        "buscar_por_id",
        lambda _id: {"id": 3, "rol": "comedor", "estado": "activo"},
    )
    monkeypatch.setattr(
        DonacionRepository,
        "crear",
        lambda *_args: pytest.fail("No debe persistir con rol incorrecto"),
    )

    with pytest.raises(HTTPException) as error:
        DonacionService.registrar_donacion(datos)

    assert error.value.status_code == 400


def test_solicitud_requiere_comedor_activo(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    datos = SolicitudCreate(
        donacion_id=20,
        comedor_id=2,
        cantidad_solicitada=1,
    )
    monkeypatch.setattr(
        UsuarioRepository,
        "buscar_por_id",
        lambda _id: {"id": 2, "rol": "negocio", "estado": "activo"},
    )
    monkeypatch.setattr(
        SolicitudRepository,
        "crear",
        lambda *_args: pytest.fail("No debe persistir con rol incorrecto"),
    )

    with pytest.raises(HTTPException) as error:
        SolicitudService.registrar_solicitud(datos)

    assert error.value.status_code == 400


def test_api_publica_requiere_clave_y_certificado_seguros(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    publico = replace(
        settings,
        api_host="0.0.0.0",
        secret_key="alimento-solidario-secret-key-demo",
        database=replace(settings.database, trust_server_certificate=True),
    )
    monkeypatch.setattr("app.main.settings", publico)

    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        validate_runtime_settings()

    segura = replace(
        publico,
        secret_key="a" * 32,
        database=replace(publico.database, trust_server_certificate=False),
    )
    monkeypatch.setattr("app.main.settings", segura)
    validate_runtime_settings()

    insegura = replace(
        segura,
        database=replace(segura.database, trust_server_certificate=True),
    )
    monkeypatch.setattr("app.main.settings", insegura)
    with pytest.raises(RuntimeError, match="DB_TRUST_SERVER_CERTIFICATE"):
        validate_runtime_settings()
