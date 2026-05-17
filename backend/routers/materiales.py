"""
Router de materiales: lista maestra — RN-07 solo admin puede crear/editar.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional

from core.database import get_conn
from core.auth import get_current_user, require_admin

router = APIRouter()


class MaterialIn(BaseModel):
    codigo: str
    nombre: str
    descripcion: Optional[str] = None
    emoji: str = "♻️"
    precio_referencial: float = 0.0
    unidad: str = "kg"
    categoria_id: Optional[int] = None

class MaterialUpdateIn(BaseModel):
    nombre: Optional[str] = None
    precio_referencial: Optional[float] = None
    emoji: Optional[str] = None
    descripcion: Optional[str] = None
    categoria_id: Optional[int] = None


def _row2dict(r):
    d = dict(r)
    for k, v in d.items():
        if hasattr(v, 'isoformat'):
            d[k] = v.isoformat()
        elif type(v).__name__ == 'UUID':
            d[k] = str(v)
        elif hasattr(v, '__float__'):
            try:
                d[k] = float(v)
            except Exception:
                pass
    return d


@router.get("/")
async def list_materiales(
    solo_activos: bool = False,
    current_user: dict = Depends(get_current_user),
):
    empresa_id = current_user["empresa_id"]
    filtro = "AND m.estado='activo'" if solo_activos else ""
    async with get_conn(empresa_id) as conn:
        rows = await conn.fetch(
            f"""
            SELECT m.id, m.codigo, m.nombre, m.descripcion, m.emoji,
                   m.precio_referencial, m.unidad, m.estado, m.created_at,
                   cat.nombre AS categoria,
                   COALESCE(i.stock_kg, 0) AS stock_kg
            FROM materiales m
            LEFT JOIN categorias_material cat ON cat.id = m.categoria_id
            LEFT JOIN inventario i ON i.material_id = m.id AND i.empresa_id = m.empresa_id
            WHERE m.empresa_id = $1 {filtro}
            ORDER BY cat.nombre, m.nombre
            """,
            empresa_id,
        )
    return [_row2dict(r) for r in rows]


@router.post("/", dependencies=[Depends(require_admin)])
async def crear_material(
    body: MaterialIn,
    request: Request,
    current_user: dict = Depends(require_admin),
):
    empresa_id = current_user["empresa_id"]
    async with get_conn(empresa_id) as conn:
        existing = await conn.fetchval(
            "SELECT id FROM materiales WHERE empresa_id=$1 AND codigo=$2",
            empresa_id, body.codigo.upper(),
        )
        if existing:
            raise HTTPException(status_code=409, detail="Ya existe un material con ese código")

        mat_id = await conn.fetchval(
            """
            INSERT INTO materiales
                (empresa_id, categoria_id, codigo, nombre, descripcion, emoji,
                 precio_referencial, unidad, created_by)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
            RETURNING id
            """,
            empresa_id, body.categoria_id, body.codigo.upper(), body.nombre,
            body.descripcion, body.emoji, body.precio_referencial, body.unidad,
            current_user["id"],
        )

        await conn.execute(
            """
            INSERT INTO audit_log
                (empresa_id, usuario_id, usuario_email, usuario_rol,
                 accion, tabla_afectada, registro_id, descripcion, ip_address)
            VALUES ($1,$2,$3,$4,'CREATE','materiales',$5,$6,$7)
            """,
            empresa_id, current_user["id"], current_user["email"],
            current_user["rol"], str(mat_id),
            f"Material creado: {body.codigo} — {body.nombre}",
            request.client.host if request.client else None,
        )

    return {"id": str(mat_id), "detail": "Material creado"}


@router.put("/{material_id}", dependencies=[Depends(require_admin)])
async def actualizar_material(
    material_id: str,
    body: MaterialUpdateIn,
    request: Request,
    current_user: dict = Depends(require_admin),
):
    empresa_id = current_user["empresa_id"]
    async with get_conn(empresa_id) as conn:
        mat = await conn.fetchrow(
            "SELECT * FROM materiales WHERE id=$1 AND empresa_id=$2",
            material_id, empresa_id,
        )
        if not mat:
            raise HTTPException(status_code=404, detail="Material no encontrado")

        datos_ant = {
            "precio": float(mat["precio_referencial"] or 0),
            "emoji": mat["emoji"],
        }

        sets, vals = [], []
        idx = 1
        if body.nombre is not None:
            sets.append(f"nombre=${idx}"); vals.append(body.nombre); idx += 1
        if body.precio_referencial is not None:
            sets.append(f"precio_referencial=${idx}"); vals.append(body.precio_referencial); idx += 1
        if body.emoji is not None:
            sets.append(f"emoji=${idx}"); vals.append(body.emoji); idx += 1
        if body.descripcion is not None:
            sets.append(f"descripcion=${idx}"); vals.append(body.descripcion); idx += 1
        if body.categoria_id is not None:
            sets.append(f"categoria_id=${idx}"); vals.append(body.categoria_id); idx += 1

        if not sets:
            return {"detail": "Nada que actualizar"}

        vals.append(material_id)
        await conn.execute(
            f"UPDATE materiales SET {', '.join(sets)} WHERE id=${idx}",
            *vals,
        )

        import json
        nuevos = body.model_dump(exclude_none=True)
        await conn.execute(
            """
            INSERT INTO audit_log
                (empresa_id, usuario_id, usuario_email, usuario_rol,
                 accion, tabla_afectada, registro_id, datos_anteriores, datos_nuevos,
                 descripcion, ip_address)
            VALUES ($1,$2,$3,$4,'UPDATE','materiales',$5,$6,$7,$8,$9)
            """,
            empresa_id, current_user["id"], current_user["email"],
            current_user["rol"], material_id,
            json.dumps(datos_ant), json.dumps(nuevos),
            f"Material actualizado: {mat['nombre']}",
            request.client.host if request.client else None,
        )

    return {"detail": "Material actualizado"}


@router.patch("/{material_id}/toggle", dependencies=[Depends(require_admin)])
async def toggle_estado(
    material_id: str,
    current_user: dict = Depends(require_admin),
):
    empresa_id = current_user["empresa_id"]
    async with get_conn(empresa_id) as conn:
        mat = await conn.fetchrow(
            "SELECT id, estado FROM materiales WHERE id=$1 AND empresa_id=$2",
            material_id, empresa_id,
        )
        if not mat:
            raise HTTPException(status_code=404, detail="Material no encontrado")

        nuevo_estado = "inactivo" if mat["estado"] == "activo" else "activo"
        await conn.execute(
            "UPDATE materiales SET estado=$1 WHERE id=$2",
            nuevo_estado, material_id,
        )
    return {"estado": nuevo_estado}


@router.get("/categorias/")
async def list_categorias(current_user: dict = Depends(get_current_user)):
    empresa_id = current_user["empresa_id"]
    async with get_conn(empresa_id) as conn:
        rows = await conn.fetch(
            "SELECT id, nombre, color_hex FROM categorias_material WHERE empresa_id=$1 AND activa=TRUE ORDER BY nombre",
            empresa_id,
        )
    return [dict(r) for r in rows]
