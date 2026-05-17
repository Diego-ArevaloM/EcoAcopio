"""
Utilidades de autenticación: JWT, bcrypt, dependencias FastAPI.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
import uuid

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from core.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from core.database import get_conn

bearer_scheme = HTTPBearer(auto_error=True)


# ── PASSWORDS ────────────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ── JWT ──────────────────────────────────────────────────────────────────────

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    jti = str(uuid.uuid4())
    to_encode.update({"exp": expire, "jti": jti})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")


# ── DEPENDENCY ───────────────────────────────────────────────────────────────

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    payload = decode_token(credentials.credentials)
    user_id    = payload.get("sub")
    empresa_id = payload.get("empresa_id")
    rol        = payload.get("rol")
    if not user_id or not empresa_id:
        raise HTTPException(status_code=401, detail="Token inválido")

    async with get_conn(empresa_id) as conn:
        user = await conn.fetchrow(
            "SELECT id, nombre, apellido, email, rol, activo FROM usuarios WHERE id=$1",
            user_id,
        )
    if not user or not user["activo"]:
        raise HTTPException(status_code=401, detail="Usuario no encontrado o inactivo")

    return {
        "id": str(user["id"]),
        "nombre": user["nombre"],
        "apellido": user["apellido"],
        "email": user["email"],
        "rol": user["rol"],
        "empresa_id": empresa_id,
    }


async def require_admin(current_user: dict = Depends(get_current_user)):
    if current_user["rol"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="🔒 Solo el Administrador puede realizar esta acción — RN-10",
        )
    return current_user
