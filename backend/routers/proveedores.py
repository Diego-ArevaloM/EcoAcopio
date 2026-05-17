"""
Router de proveedores — RN-08 unicidad documento, RN-09 proveedor anónimo.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional

from core.database import get_conn
from core.auth import get_current_user, require_admin

router = APIRouter()


class ProveedorIn(BaseModel):
    nombre: str
    tipo_documento: Optional[str] = None    # DNI, RUC, PASAPORTE, CE
    numero_documento: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    direccion: Optional[str] = None


def _row2dict(r):
    d = dict(r)
    for k, v in d.items():
        if hasattr(v, 'isoformat'):
            d[k] = v.isoformat()
        elif type(v).__name__ == 'UUID':
            d[k] = str(v)
    return d


@router.get("/")
async def list_proveedores(current_user: dict = Depends(get_current_user)):
    empresa_id = current_user["empresa_id"]
    async with get_conn(empresa_id) as conn:
        rows = await conn.fetch(
            """
            SELECT p.id, p.nombre, p.tipo_documento, p.numero_documento,
                   p.telefono, p.email, p.es_anonimo, p.activo,
                   COUNT(px.id) AS total_transacciones
            FROM proveedores p
            LEFT JOIN pesajes px ON px.proveedor_id = p.id AND NOT px.anulado
            WHERE p.empresa_id = $1
            GROUP BY p.id
            ORDER BY p.es_anonimo DESC, p.nombre
            """,
            empresa_id,
        )
    return [_row2dict(r) for r in rows]


@router.post("/")
async def crear_proveedor(
    body: ProveedorIn,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    empresa_id = current_user["empresa_id"]

    # RN-09: no se puede crear proveedor anónimo manualmente
    if not body.nombre.strip():
        raise HTTPException(status_code=422, detail="El nombre es obligatorio")

    async with get_conn(empresa_id) as conn:
        if body.numero_documento:
            # RN-08: unicidad de documento
            existing = await conn.fetchval(
                "SELECT id FROM proveedores WHERE empresa_id=$1 AND numero_documento=$2",
                empresa_id, body.numero_documento,
            )
            if existing:
                raise HTTPException(
                    status_code=409,
                    detail="🚫 RN-08: Ya existe un proveedor con ese número de documento",
                )

        prov_id = await conn.fetchval(
            """
            INSERT INTO proveedores
                (empresa_id, nombre, tipo_documento, numero_documento,
                 telefono, email, direccion)
            VALUES ($1,$2,$3,$4,$5,$6,$7)
            RETURNING id
            """,
            empresa_id, body.nombre, body.tipo_documento,
            body.numero_documento, body.telefono, body.email, body.direccion,
        )

    return {"id": str(prov_id), "detail": "Proveedor registrado"}


@router.put("/{proveedor_id}")
async def actualizar_proveedor(
    proveedor_id: str,
    body: ProveedorIn,
    current_user: dict = Depends(get_current_user),
):
    empresa_id = current_user["empresa_id"]
    async with get_conn(empresa_id) as conn:
        prov = await conn.fetchrow(
            "SELECT * FROM proveedores WHERE id=$1 AND empresa_id=$2",
            proveedor_id, empresa_id,
        )
        if not prov:
            raise HTTPException(status_code=404, detail="Proveedor no encontrado")

        # RN-09: proveedor anónimo es inmodificable
        if prov["es_anonimo"]:
            raise HTTPException(
                status_code=403,
                detail="🔒 RN-09: El proveedor anónimo es inmodificable",
            )

        await conn.execute(
            """
            UPDATE proveedores
            SET nombre=$1, tipo_documento=$2, numero_documento=$3,
                telefono=$4, email=$5, direccion=$6
            WHERE id=$7
            """,
            body.nombre, body.tipo_documento, body.numero_documento,
            body.telefono, body.email, body.direccion, proveedor_id,
        )
    return {"detail": "Proveedor actualizado"}


@router.delete("/{proveedor_id}", dependencies=[Depends(require_admin)])
async def eliminar_proveedor(
    proveedor_id: str,
    current_user: dict = Depends(require_admin),
):
    empresa_id = current_user["empresa_id"]
    async with get_conn(empresa_id) as conn:
        prov = await conn.fetchrow(
            "SELECT es_anonimo FROM proveedores WHERE id=$1 AND empresa_id=$2",
            proveedor_id, empresa_id,
        )
        if not prov:
            raise HTTPException(status_code=404, detail="Proveedor no encontrado")
        if prov["es_anonimo"]:
            raise HTTPException(status_code=403, detail="🔒 RN-09: No se puede eliminar el proveedor anónimo")

        # Soft delete: marcar inactivo (hay transacciones históricas)
        await conn.execute(
            "UPDATE proveedores SET activo=FALSE WHERE id=$1", proveedor_id
        )
    return {"detail": "Proveedor desactivado"}
