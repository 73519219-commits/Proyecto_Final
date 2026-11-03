from __future__ import annotations

from typing import Any

from app.core.seguridad import hash_password

usuarios: list[dict[str, Any]] = []
donaciones: list[dict[str, Any]] = []
solicitudes: list[dict[str, Any]] = []
entregas: list[dict[str, Any]] = []


def reset_demo_data() -> None:
    """Inicializa datos de prueba en memoria para demostración académica."""
    global usuarios, donaciones, solicitudes, entregas

    usuarios = [
        {
            "id": 1,
            "nombres": "Administrador",
            "apellidos": "Sistema",
            "correo": "admin@alimentosolidario.pe",
            "password_hash": hash_password("admin123"),
            "telefono": "987654321",
            "direccion": "Jr. Puno 120",
            "rol": "admin",
            "estado": "activo",
        },
        {
            "id": 2,
            "nombres": "Panadería",
            "apellidos": "San José",
            "correo": "negocio@panaderia.pe",
            "password_hash": hash_password("negocio123"),
            "telefono": "961234567",
            "direccion": "Av. Real 320",
            "rol": "negocio",
            "estado": "activo",
        },
        {
            "id": 3,
            "nombres": "Comedor",
            "apellidos": "Esperanza",
            "correo": "comedor@esperanza.pe",
            "password_hash": hash_password("comedor123"),
            "telefono": "991122334",
            "direccion": "Jr. Progreso 80",
            "rol": "comedor",
            "estado": "activo",
        },
        {
            "id": 4,
            "nombres": "Carlos",
            "apellidos": "Ruiz",
            "correo": "voluntario@correo.pe",
            "password_hash": hash_password("voluntario123"),
            "telefono": "965432100",
            "direccion": "Urb. San Martín",
            "rol": "voluntario",
            "estado": "activo",
        },
    ]

    donaciones = [
        {
            "id": 1,
            "nombre_alimento": "Pan de trigo",
            "descripcion": "Pan recién horneado en buen estado.",
            "cantidad": 40,
            "unidad": "unidad",
            "fecha_vencimiento": "2026-11-10",
            "direccion_recojo": "Av. Real 320",
            "hora_disponible": "08:00 - 10:00",
            "estado": "disponible",
            "usuario_negocio_id": 2,
        },
        {
            "id": 2,
            "nombre_alimento": "Arroz",
            "descripcion": "Sacos de arroz sin daños en empaque.",
            "cantidad": 20,
            "unidad": "kg",
            "fecha_vencimiento": "2026-11-18",
            "direccion_recojo": "Av. Real 320",
            "hora_disponible": "09:00 - 12:00",
            "estado": "disponible",
            "usuario_negocio_id": 2,
        },
    ]

    solicitudes = [
        {
            "id": 1,
            "donacion_id": 1,
            "comedor_id": 3,
            "cantidad_solicitada": 10,
            "estado": "pendiente",
        }
    ]

    entregas = [
        {
            "id": 1,
            "solicitud_id": 1,
            "voluntario_id": 4,
            "fecha_asignacion": "2026-11-02",
            "fecha_entrega": "2026-11-03",
            "estado": "asignada",
            "observaciones": "Entrega coordinada con la familia del comedor.",
        }
    ]


reset_demo_data()
