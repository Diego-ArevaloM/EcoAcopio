"""
Router de autenticación: login, logout, me, registro (admin).
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, EmailStr
import uuid

from core.database import get_conn
from core.auth import (
    verify_password, hash_password, create_access_token,
    get_current_user, require_admin,
)

router = APIRouter()


# ── SCHEMAS ──────────────────────────────────────────────────────────────────

class LoginIn(BaseModel):
    email: str
    password: str

class RegisterIn(BaseModel):
    nombre: str
    apellido: str
    email: EmailStr
    password: str
    rol: str = "operario"

class ChangePasswordIn(BaseModel):
    current_password: str
    new_password: str


# ── ENDPOINTS ────────────────────────────────────────────────────────────────

@router.post("/login")
async def login(body: LoginIn, request: Request):
    # Buscamos en todas las empresas (luego RLS aplica por empresa_id en cada petición)
    async with get_conn() as conn:
        user = await conn.fetchrow(
            """
            SELECT u.id, u.empresa_id, u.nombre, u.apellido, u.email,
                   u.password_hash, u.rol, u.activo
            FROM usuarios u
            WHERE u.email = $1
            LIMIT 1
            """,
            body.email,
        )

    if not user:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    if not user["activo"]:
        raise HTTPException(status_code=403, detail="Usuario inactivo")
    if not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    empresa_id = str(user["empresa_id"])
    token = create_access_token({
        "sub": str(user["id"]),
        "empresa_id": empresa_id,
        "rol": user["rol"],
        "email": user["email"],
    })

    # Actualizar ultimo_login + audit
    async with get_conn(empresa_id) as conn:
        await conn.execute(
            "UPDATE usuarios SET ultimo_login = NOW() WHERE id = $1",
            user["id"],
        )
        await conn.execute(
            """
            INSERT INTO audit_log
                (empresa_id, usuario_id, usuario_email, usuario_rol, accion,
                 tabla_afectada, descripcion, ip_address)
            VALUES ($1,$2,$3,$4,'LOGIN','usuarios','Inicio de sesión',$5)
            """,
            user["empresa_id"], user["id"], user["email"], user["rol"],
            request.client.host if request.client else None,
        )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": str(user["id"]),
            "nombre": user["nombre"],
            "apellido": user["apellido"],
            "email": user["email"],
            "rol": user["rol"],
            "empresa_id": empresa_id,
        },
    }


@router.get("/me")
async def me(current_user: dict = Depends(get_current_user)):
    return current_user


@router.post("/logout")
async def logout(request: Request, current_user: dict = Depends(get_current_user)):
    async with get_conn(current_user["empresa_id"]) as conn:
        await conn.execute(
            """
            INSERT INTO audit_log
                (empresa_id, usuario_id, usuario_email, usuario_rol, accion,
                 tabla_afectada, descripcion, ip_address)
            VALUES ($1,$2,$3,$4,'LOGOUT','usuarios','Cierre de sesión',$5)
            """,
            current_user["empresa_id"], current_user["id"],
            current_user["email"], current_user["rol"],
            request.client.host if request.client else None,
        )
    return {"detail": "Sesión cerrada"}


@router.post("/register", dependencies=[Depends(require_admin)])
async def register(body: RegisterIn, current_user: dict = Depends(require_admin)):
    if body.rol not in ("admin", "operario"):
        raise HTTPException(status_code=422, detail="Rol inválido")

    empresa_id = current_user["empresa_id"]
    pw_hash = hash_password(body.password)

    async with get_conn(empresa_id) as conn:
        existing = await conn.fetchrow(
            "SELECT id FROM usuarios WHERE email=$1 AND empresa_id=$2",
            body.email, empresa_id,
        )
        if existing:
            raise HTTPException(status_code=409, detail="Email ya registrado en esta empresa")

        new_id = await conn.fetchval(
            """
            INSERT INTO usuarios (empresa_id, nombre, apellido, email, password_hash, rol)
            VALUES ($1,$2,$3,$4,$5,$6) RETURNING id
            """,
            empresa_id, body.nombre, body.apellido, body.email, pw_hash, body.rol,
        )

    return {"id": str(new_id), "email": body.email, "rol": body.rol}


@router.put("/change-password")
async def change_password(
    body: ChangePasswordIn,
    current_user: dict = Depends(get_current_user),
):
    async with get_conn(current_user["empresa_id"]) as conn:
        user = await conn.fetchrow(
            "SELECT password_hash FROM usuarios WHERE id=$1", current_user["id"]
        )
        if not verify_password(body.current_password, user["password_hash"]):
            raise HTTPException(status_code=400, detail="Contraseña actual incorrecta")
        new_hash = hash_password(body.new_password)
        await conn.execute(
            "UPDATE usuarios SET password_hash=$1 WHERE id=$2",
            new_hash, current_user["id"],
        )
    return {"detail": "Contraseña actualizada"}
