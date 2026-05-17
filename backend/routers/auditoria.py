"""
Router de auditoría — RN-12 log inmutable.
CORRECCIÓN: eliminada interpolación de string en SQL (vulnerabilidad de inyección).
"""
from fastapi import APIRouter, Depends
from typing import Optional

from core.database import get_conn
from core.auth import require_admin

router = APIRouter()


def _row2dict(r):
    d = dict(r)
    for k, v in d.items():
        if hasattr(v, 'isoformat'):
            d[k] = v.isoformat()
        elif type(v).__name__ == 'UUID':
            d[k] = str(v)
    return d


@router.get("/")
async def get_audit_log(
    limit: int = 100,
    offset: int = 0,
    accion: Optional[str] = None,
    current_user: dict = Depends(require_admin),
):
    empresa_id = current_user["empresa_id"]

    async with get_conn(empresa_id) as conn:
        if accion:
            rows = await conn.fetch(
                """
                SELECT id, usuario_email, usuario_rol, accion, tabla_afectada,
                       registro_id, descripcion, created_at, ip_address
                FROM audit_log
                WHERE empresa_id=$1 AND accion=$2
                ORDER BY created_at DESC
                LIMIT $3 OFFSET $4
                """,
                empresa_id, accion, limit, offset,
            )
            total = await conn.fetchval(
                "SELECT COUNT(*) FROM audit_log WHERE empresa_id=$1 AND accion=$2",
                empresa_id, accion,
            )
        else:
            rows = await conn.fetch(
                """
                SELECT id, usuario_email, usuario_rol, accion, tabla_afectada,
                       registro_id, descripcion, created_at, ip_address
                FROM audit_log
                WHERE empresa_id=$1
                ORDER BY created_at DESC
                LIMIT $2 OFFSET $3
                """,
                empresa_id, limit, offset,
            )
            total = await conn.fetchval(
                "SELECT COUNT(*) FROM audit_log WHERE empresa_id=$1",
                empresa_id,
            )

        resumen = await conn.fetch(
            """
            SELECT accion, COUNT(*) AS cnt
            FROM audit_log
            WHERE empresa_id=$1
            GROUP BY accion
            ORDER BY cnt DESC
            """,
            empresa_id,
        )
        hoy = await conn.fetchval(
            """
            SELECT COUNT(*) FROM audit_log
            WHERE empresa_id=$1
              AND DATE(created_at AT TIME ZONE 'America/Lima') = CURRENT_DATE
            """,
            empresa_id,
        )

    return {
        "total": total,
        "hoy": hoy,
        "items": [_row2dict(r) for r in rows],
        "resumen": [{"accion": r["accion"], "cnt": r["cnt"]} for r in resumen],
    }
