"""
Router de reportes — RN-13 cierres mensuales inmutables, exportación CSV.
"""
import csv
import io
import json
import hashlib
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

from core.database import get_conn
from core.auth import require_admin

router = APIRouter()


class CerrarMesIn(BaseModel):
    mes: int
    año: int


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
async def generar_reporte(
    mes: int,
    año: int,
    current_user: dict = Depends(require_admin),
):
    empresa_id = current_user["empresa_id"]

    async with get_conn(empresa_id) as conn:
        # Verificar si hay cierre para este período
        cierre = await conn.fetchrow(
            "SELECT * FROM cierres_mensuales WHERE empresa_id=$1 AND mes=$2 AND año=$3",
            empresa_id, mes, año,
        )

        # Transacciones del período
        rows = await conn.fetch(
            """
            SELECT p.id, p.tipo, p.peso_kg, p.total_valor, p.observaciones,
                   p.registrado_en, p.anulado, p.modificado,
                   m.nombre AS material, m.emoji, m.codigo,
                   pr.nombre AS proveedor,
                   u.nombre || ' ' || u.apellido AS operario
            FROM pesajes p
            JOIN materiales m ON m.id = p.material_id
            JOIN proveedores pr ON pr.id = p.proveedor_id
            JOIN usuarios u ON u.id = p.operario_id
            WHERE p.empresa_id = $1
              AND EXTRACT(MONTH FROM p.registrado_en AT TIME ZONE 'America/Lima') = $2
              AND EXTRACT(YEAR  FROM p.registrado_en AT TIME ZONE 'America/Lima') = $3
            ORDER BY p.registrado_en
            """,
            empresa_id, mes, año,
        )

        # Estadísticas
        stats = await conn.fetchrow(
            """
            SELECT
                COALESCE(SUM(peso_kg) FILTER (WHERE tipo='entrada' AND NOT anulado), 0) AS total_entradas_kg,
                COALESCE(SUM(peso_kg) FILTER (WHERE tipo='salida'  AND NOT anulado), 0) AS total_salidas_kg,
                COUNT(*)                                                                  AS total_transacciones,
                COUNT(*) FILTER (WHERE modificado)                                        AS modificados,
                COALESCE(SUM(total_valor) FILTER (WHERE NOT anulado), 0)                 AS valor_total
            FROM pesajes
            WHERE empresa_id = $1
              AND EXTRACT(MONTH FROM registrado_en AT TIME ZONE 'America/Lima') = $2
              AND EXTRACT(YEAR  FROM registrado_en AT TIME ZONE 'America/Lima') = $3
            """,
            empresa_id, mes, año,
        )

    items = [_row2dict(r) for r in rows]

    return {
        "periodo": {"mes": mes, "año": año},
        "cierre": _row2dict(cierre) if cierre else None,
        "stats": {
            "total_entradas_kg": float(stats["total_entradas_kg"]),
            "total_salidas_kg": float(stats["total_salidas_kg"]),
            "balance_kg": float(stats["total_entradas_kg"]) - float(stats["total_salidas_kg"]),
            "total_transacciones": stats["total_transacciones"],
            "modificados": stats["modificados"],
            "valor_total": float(stats["valor_total"]),
            "alterado": bool(cierre and cierre["alterado"]) if cierre else bool(stats["modificados"] > 0),
        },
        "transacciones": items,
    }


@router.post("/cerrar")
async def cerrar_mes(
    body: CerrarMesIn,
    current_user: dict = Depends(require_admin),
):
    empresa_id = current_user["empresa_id"]

    async with get_conn(empresa_id) as conn:
        existing = await conn.fetchrow(
            "SELECT id, estado FROM cierres_mensuales WHERE empresa_id=$1 AND mes=$2 AND año=$3",
            empresa_id, body.mes, body.año,
        )
        if existing and existing["estado"] == "cerrado":
            raise HTTPException(status_code=409, detail="Este período ya está cerrado — RN-13")

        # Snapshot de transacciones
        rows = await conn.fetch(
            """
            SELECT p.id::text, p.tipo, p.peso_kg::float, p.total_valor::float,
                   p.registrado_en::text, p.anulado
            FROM pesajes p
            WHERE empresa_id=$1
              AND EXTRACT(MONTH FROM registrado_en AT TIME ZONE 'America/Lima') = $2
              AND EXTRACT(YEAR  FROM registrado_en AT TIME ZONE 'America/Lima') = $3
            """,
            empresa_id, body.mes, body.año,
        )

        stats = await conn.fetchrow(
            """
            SELECT
                COALESCE(SUM(peso_kg) FILTER (WHERE tipo='entrada' AND NOT anulado), 0) AS ent,
                COALESCE(SUM(peso_kg) FILTER (WHERE tipo='salida'  AND NOT anulado), 0) AS sal,
                COUNT(*) AS txs
            FROM pesajes
            WHERE empresa_id=$1
              AND EXTRACT(MONTH FROM registrado_en AT TIME ZONE 'America/Lima') = $2
              AND EXTRACT(YEAR  FROM registrado_en AT TIME ZONE 'America/Lima') = $3
            """,
            empresa_id, body.mes, body.año,
        )

        snapshot = json.dumps([dict(r) for r in rows], default=str)
        hash_sha = hashlib.sha256(snapshot.encode()).hexdigest()

        if existing:
            cierre_id = await conn.fetchval(
                """
                UPDATE cierres_mensuales
                SET estado='cerrado', total_entradas_kg=$1, total_salidas_kg=$2,
                    total_transacciones=$3, hash_integridad=$4, snapshot_json=$5,
                    cerrado_en=NOW(), cerrado_por=$6
                WHERE id=$7 RETURNING id
                """,
                float(stats["ent"]), float(stats["sal"]), stats["txs"],
                hash_sha, snapshot, current_user["id"], existing["id"],
            )
        else:
            cierre_id = await conn.fetchval(
                """
                INSERT INTO cierres_mensuales
                    (empresa_id, mes, año, estado, total_entradas_kg, total_salidas_kg,
                     total_transacciones, hash_integridad, snapshot_json, cerrado_en, cerrado_por)
                VALUES ($1,$2,$3,'cerrado',$4,$5,$6,$7,$8,NOW(),$9)
                RETURNING id
                """,
                empresa_id, body.mes, body.año,
                float(stats["ent"]), float(stats["sal"]), stats["txs"],
                hash_sha, snapshot, current_user["id"],
            )

    return {"id": str(cierre_id), "detail": f"Período {body.mes}/{body.año} cerrado correctamente"}


@router.get("/exportar-csv")
async def exportar_csv(
    mes: int,
    año: int,
    current_user: dict = Depends(require_admin),
):
    empresa_id = current_user["empresa_id"]
    async with get_conn(empresa_id) as conn:
        rows = await conn.fetch(
            """
            SELECT p.id, p.tipo, p.peso_kg, p.total_valor, p.observaciones,
                   p.registrado_en, p.anulado, p.modificado,
                   m.codigo, m.nombre AS material, m.emoji,
                   pr.nombre AS proveedor,
                   u.nombre || ' ' || u.apellido AS operario
            FROM pesajes p
            JOIN materiales m ON m.id = p.material_id
            JOIN proveedores pr ON pr.id = p.proveedor_id
            JOIN usuarios u ON u.id = p.operario_id
            WHERE p.empresa_id=$1
              AND EXTRACT(MONTH FROM p.registrado_en AT TIME ZONE 'America/Lima')=$2
              AND EXTRACT(YEAR  FROM p.registrado_en AT TIME ZONE 'America/Lima')=$3
            ORDER BY p.registrado_en
            """,
            empresa_id, mes, año,
        )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "Fecha", "Tipo", "Material (Código)", "Material (Nombre)",
        "Proveedor", "Peso (kg)", "Valor (S/.)", "Operario", "Anulado", "Modificado", "Observaciones",
    ])
    for r in rows:
        writer.writerow([
            str(r["id"]),
            r["registrado_en"].strftime("%d/%m/%Y %H:%M:%S") if r["registrado_en"] else "",
            r["tipo"],
            r["codigo"],
            r["material"],
            r["proveedor"],
            f"{float(r['peso_kg']):.3f}",
            f"{float(r['total_valor']):.2f}" if r["total_valor"] else "0.00",
            r["operario"],
            "SÍ" if r["anulado"] else "NO",
            "SÍ" if r["modificado"] else "NO",
            r["observaciones"] or "",
        ])

    output.seek(0)
    filename = f"ecoaCopio_reporte_{mes:02d}_{año}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8-sig",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
