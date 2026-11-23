from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.seguridad import create_access_token, get_current_user, require_roles
from app.schemas.usuario import (
    RolDto,
    UsuarioCreate,
    UsuarioLogin,
    UsuarioLoginResponse,
    UsuarioOut,
    UsuarioUpdate,
)
from app.services.usuario_service import UsuarioService

router = APIRouter(prefix="/api", tags=["usuarios"])


@router.post("/auth/registro", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
def registrar_usuario(usuario: UsuarioCreate):
    return UsuarioService.registrar_usuario(usuario)


@router.post("/auth/login", response_model=UsuarioLoginResponse)
def login(usuario_login: UsuarioLogin):
    usuario = UsuarioService.autenticar(usuario_login)
    token = create_access_token(
        {
            "sub": str(usuario["id"]),
            "correo": usuario["correo"],
            "rol": usuario["rol"],
        }
    )
    return {"access_token": token, "token_type": "bearer", "usuario": usuario}


@router.get("/usuarios", response_model=list[UsuarioOut])
def listar_usuarios(
    rol: RolDto | None = Query(default=None),
    _: dict = Depends(require_roles(["admin"])),
):
    return UsuarioService.listar_usuarios(rol)


@router.get("/usuarios/me", response_model=UsuarioOut)
def obtener_mi_perfil(usuario_actual: dict = Depends(get_current_user)):
    return UsuarioService.buscar_por_id(usuario_actual["id"])


@router.patch("/usuarios/me/disponible", response_model=UsuarioOut)
def actualizar_disponibilidad(
    disponible: bool,
    usuario_actual: dict = Depends(require_roles(["voluntario"])),
):
    return UsuarioService.actualizar_usuario(
        usuario_actual["id"],
        UsuarioUpdate(disponible=disponible),
    )


@router.put("/usuarios/{usuario_id}", response_model=UsuarioOut)
@router.patch("/usuarios/{usuario_id}", response_model=UsuarioOut)
def actualizar_usuario(
    usuario_id: int,
    datos: UsuarioUpdate,
    _: dict = Depends(require_roles(["admin"])),
):
    return UsuarioService.actualizar_usuario(usuario_id, datos)


@router.delete("/usuarios/{usuario_id}")
def eliminar_usuario(
    usuario_id: int,
    _: dict = Depends(require_roles(["admin"])),
):
    return UsuarioService.eliminar_usuario(usuario_id)


