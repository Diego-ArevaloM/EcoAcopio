"""
Router de pesajes: registro de entradas y salidas de material.
RN-01 peso>0, RN-03 timestamp servidor, RN-04 alerta 5000kg, RN-06 stock≥0.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, field_validator
from typing import Optional
import uuid

from core.database import get_conn
from core.auth import get_current_user, require_admin
from core.config import LIMITE_PESO_ALERTA_KG

router = APIRouter()


# ── SCHEMAS ──────────────────────────────────────────────────────────────────

class PesajeIn(BaseModel):
    material_id: str
    proveedor_id: str
    tipo: str                   # 'entrada' | 'salida'
    peso_kg: float
    precio_unitario: Optional[float] = None
    observaciones: Optional[str] = None
    confirmar_alerta: bool = False   # True cuando el usuario acepta RN-04

    @field_validator("peso_kg")
    @classmethod
    def peso_positivo(cls, v):
        if v <= 0:
            raise ValueError("RN-01: El peso debe ser mayor a cero")
        return v

    @field_validator("tipo")
    @classmethod
    def tipo_valido(cls, v):
        if v not in ("entrada", "salida"):
            raise ValueError("Tipo debe ser 'entrada' o 'salida'")
        return v

class AnularPesajeIn(BaseModel):
    motivo: Optional[str] = None


# ── HELPERS ──────────────────────────────────────────────────────────────────

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


# ── ENDPOINTS ────────────────────────────────────────────────────────────────

@router.get("/")
async def list_pesajes(
    limit: int = 50,
    offset: int = 0,
    tipo: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    empresa_id = current_user["empresa_id"]
    tipo_filter = f"AND p.tipo = '{tipo}'" if tipo in ("entrada", "salida") else ""

    async with get_conn(empresa_id) as conn:
        rows = await conn.fetch(
            f"""
            SELECT p.id, m.nombre AS material, m.emoji, pr.nombre AS proveedor,
                   p.peso_kg, p.precio_unitario, p.total_valor, p.tipo,
                   p.observaciones, p.registrado_en, p.anulado, p.modificado,
                   u.nombre || ' ' || u.apellido AS operario
            FROM pesajes p
            JOIN materiales m ON m.id = p.material_id
            JOIN proveedores pr ON pr.id = p.proveedor_id
            JOIN usuarios u ON u.id = p.operario_id
            WHERE p.empresa_id = $1 {tipo_filter}
            ORDER BY p.registrado_en DESC
            LIMIT $2 OFFSET $3
            """,
            empresa_id, limit, offset,
        )
        total = await conn.fetchval(
            f"SELECT COUNT(*) FROM pesajes WHERE empresa_id=$1 {tipo_filter.replace('p.tipo','tipo')}",
            empresa_id,
        )

    return {"total": total, "items": [_row2dict(r) for r in rows]}


@router.post("/")
async def crear_pesaje(
    body: PesajeIn,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    empresa_id = current_user["empresa_id"]

    # RN-04: alerta de peso > límite
    if body.peso_kg > LIMITE_PESO_ALERTA_KG and not body.confirmar_alerta:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "RN-04",
                "message": f"El peso ({body.peso_kg} kg) supera el límite de alerta ({LIMITE_PESO_ALERTA_KG} kg). Confirma para continuar.",
                "requires_confirmation": True,
            },
        )

    async with get_conn(empresa_id) as conn:
        # Validar material existe y activo
        mat = await conn.fetchrow(
            "SELECT id, nombre, precio_referencial FROM materiales WHERE id=$1 AND empresa_id=$2 AND estado='activo'",
            body.material_id, empresa_id,
        )
        if not mat:
            raise HTTPException(status_code=404, detail="Material no encontrado o inactivo — RN-07")

        # Validar proveedor
        prov = await conn.fetchrow(
            "SELECT id FROM proveedores WHERE id=$1 AND empresa_id=$2 AND activo=TRUE",
            body.proveedor_id, empresa_id,
        )
        if not prov:
            raise HTTPException(status_code=404, detail="Proveedor no encontrado o inactivo")

        precio = body.precio_unitario if body.precio_unitario is not None else float(mat["precio_referencial"] or 0)

        try:
            pesaje_id = await conn.fetchval(
                """
                INSERT INTO pesajes
                    (empresa_id, material_id, proveedor_id, operario_id,
                     tipo, peso_kg, precio_unitario, observaciones)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
                RETURNING id
                """,
                empresa_id, body.material_id, body.proveedor_id,
                current_user["id"], body.tipo, body.peso_kg, precio, body.observaciones,
            )
        except Exception as e:
            err = str(e)
            if "RN-06" in err or "stock" in err.lower():
                raise HTTPException(status_code=409, detail=err)
            raise HTTPException(status_code=500, detail=str(e))

        # Registrar en audit_log si es salida (más crítico)
        if body.tipo == "salida":
            await conn.execute(
                """
                INSERT INTO audit_log
                    (empresa_id, usuario_id, usuario_email, usuario_rol,
                     accion, tabla_afectada, registro_id, descripcion, ip_address)
                VALUES ($1,$2,$3,$4,'CREATE','pesajes',$5,$6,$7)
                """,
                empresa_id, current_user["id"], current_user["email"],
                current_user["rol"], str(pesaje_id),
                f"Salida registrada: {body.peso_kg} kg de material_id={body.material_id}",
                request.client.host if request.client else None,
            )

    return {"id": str(pesaje_id), "detail": "Pesaje registrado correctamente"}


@router.get("/{pesaje_id}")
async def get_pesaje(pesaje_id: str, current_user: dict = Depends(get_current_user)):
    empresa_id = current_user["empresa_id"]
    async with get_conn(empresa_id) as conn:
        row = await conn.fetchrow(
            """
            SELECT p.*, m.nombre AS material_nombre, m.emoji,
                   pr.nombre AS proveedor_nombre,
                   u.nombre || ' ' || u.apellido AS operario
            FROM pesajes p
            JOIN materiales m ON m.id = p.material_id
            JOIN proveedores pr ON pr.id = p.proveedor_id
            JOIN usuarios u ON u.id = p.operario_id
            WHERE p.id=$1 AND p.empresa_id=$2
            """,
            pesaje_id, empresa_id,
        )
    if not row:
        raise HTTPException(status_code=404, detail="Pesaje no encontrado")
    return _row2dict(row)


@router.put("/{pesaje_id}/anular", dependencies=[Depends(require_admin)])
async def anular_pesaje(
    pesaje_id: str,
    body: AnularPesajeIn,
    request: Request,
    current_user: dict = Depends(require_admin),
):
    empresa_id = current_user["empresa_id"]
    async with get_conn(empresa_id) as conn:
        pesaje = await conn.fetchrow(
            "SELECT * FROM pesajes WHERE id=$1 AND empresa_id=$2", pesaje_id, empresa_id
        )
        if not pesaje:
            raise HTTPException(status_code=404, detail="Pesaje no encontrado")
        if pesaje["anulado"]:
            raise HTTPException(status_code=409, detail="El pesaje ya está anulado")

        await conn.execute(
            """
            UPDATE pesajes
            SET anulado=TRUE, anulado_en=NOW(), anulado_por=$1,
                observaciones = COALESCE(observaciones,'') || ' [ANULADO: ' || $2 || ']'
            WHERE id=$3
            """,
            current_user["id"], body.motivo or "Sin motivo", pesaje_id,
        )

        await conn.execute(
            """
            INSERT INTO audit_log
                (empresa_id, usuario_id, usuario_email, usuario_rol,
                 accion, tabla_afectada, registro_id, datos_anteriores, descripcion, ip_address)
            VALUES ($1,$2,$3,$4,'ANULACION','pesajes',$5,$6,$7,$8)
            """,
            empresa_id, current_user["id"], current_user["email"], current_user["rol"],
            pesaje_id,
            '{"anulado": false}',
            f"Anulación de pesaje. Motivo: {body.motivo or 'Sin motivo'}",
            request.client.host if request.client else None,
        )

    return {"detail": "Pesaje anulado correctamente"}
