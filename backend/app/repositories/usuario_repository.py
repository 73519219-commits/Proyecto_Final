from __future__ import annotations

from typing import Any

from app.data.memoria import usuarios


class UsuarioRepository:
    @staticmethod
    def listar() -> list[dict[str, Any]]:
        return [usuario.copy() for usuario in usuarios]

    @staticmethod
    def buscar_por_id(usuario_id: int) -> dict[str, Any] | None:
        for usuario in usuarios:
            if usuario["id"] == usuario_id:
                return usuario.copy()
        return None

    @staticmethod
    def buscar_por_correo(correo: str) -> dict[str, Any] | None:
        for usuario in usuarios:
            if usuario["correo"].lower() == correo.lower():
                return usuario.copy()
        return None

    @staticmethod
    def crear(usuario: dict[str, Any]) -> dict[str, Any]:
        nuevo_id = max((item["id"] for item in usuarios), default=0) + 1
        usuario_con_id = {"id": nuevo_id, **usuario}
        usuarios.append(usuario_con_id)
        return usuario_con_id.copy()

    @staticmethod
    def actualizar(usuario_id: int, datos: dict[str, Any]) -> dict[str, Any] | None:
        for index, usuario in enumerate(usuarios):
            if usuario["id"] == usuario_id:
                usuarios[index].update(datos)
                return usuarios[index].copy()
        return None

    @staticmethod
    def eliminar(usuario_id: int) -> bool:
        for index, usuario in enumerate(usuarios):
            if usuario["id"] == usuario_id:
                usuarios[index]["estado"] = "inactivo"
                return True
        return False
