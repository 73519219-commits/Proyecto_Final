from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status

from app.core.seguridad import hash_password, verify_password
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.usuario import UsuarioCreate, UsuarioLogin, UsuarioUpdate


class UsuarioService:
    @staticmethod
    def registrar_usuario(datos: UsuarioCreate) -> dict[str, Any]:
        existe = UsuarioRepository.buscar_por_correo(datos.correo)
        if existe:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El correo ya está registrado.",
            )

        usuario = {
            "nombres": datos.nombres,
            "apellidos": datos.apellidos,
            "correo": datos.correo,
            "password_hash": hash_password(datos.password),
            "telefono": datos.telefono,
            "direccion": datos.direccion,
            "rol": datos.rol,
            "estado": datos.estado,
        }

        creado = UsuarioRepository.crear(usuario)
        creado.pop("password_hash", None)
        return creado

    @staticmethod
    def listar_usuarios() -> list[dict[str, Any]]:
        usuarios = UsuarioRepository.listar()
        for usuario in usuarios:
            usuario.pop("password_hash", None)
        return usuarios

    @staticmethod
    def buscar_por_id(usuario_id: int) -> dict[str, Any]:
        usuario = UsuarioRepository.buscar_por_id(usuario_id)
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado.")
        usuario.pop("password_hash", None)
        return usuario

    @staticmethod
    def actualizar_usuario(usuario_id: int, datos: UsuarioUpdate) -> dict[str, Any]:
        usuario_actual = UsuarioRepository.buscar_por_id(usuario_id)
        if not usuario_actual:
            raise HTTPException(status_code=404, detail="Usuario no encontrado.")

        cambios: dict[str, Any] = {}
        for campo, valor in datos.model_dump(exclude_unset=True).items():
            if valor is None:
                continue
            if campo == "password":
                cambios["password_hash"] = hash_password(valor)
            else:
                cambios[campo] = valor

        actualizado = UsuarioRepository.actualizar(usuario_id, cambios)
        if not actualizado:
            raise HTTPException(status_code=404, detail="No se pudo actualizar el usuario.")
        actualizado.pop("password_hash", None)
        return actualizado

    @staticmethod
    def eliminar_usuario(usuario_id: int) -> dict[str, str]:
        usuario = UsuarioRepository.buscar_por_id(usuario_id)
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado.")
        eliminado = UsuarioRepository.eliminar(usuario_id)
        if not eliminado:
            raise HTTPException(status_code=400, detail="No se pudo desactivar el usuario.")
        return {"mensaje": "Usuario desactivado correctamente."}

    @staticmethod
    def autenticar(datos: UsuarioLogin) -> dict[str, Any]:
        usuario = UsuarioRepository.buscar_por_correo(datos.correo)
        if not usuario or usuario.get("estado") == "inactivo":
            raise HTTPException(status_code=401, detail="Credenciales inválidas.")

        if not verify_password(datos.password, usuario["password_hash"]):
            raise HTTPException(status_code=401, detail="Credenciales inválidas.")

        usuario_sin_password = usuario.copy()
        usuario_sin_password.pop("password_hash", None)
        return usuario_sin_password
