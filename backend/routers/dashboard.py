"""
Router del Dashboard: estadísticas del día, últimas transacciones, alertas.
"""
from fastapi import APIRouter, Depends
from core.database import get_conn
from core.auth import get_current_user

router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    empresa_id = current_user["empresa_id"]

    async with get_conn(empresa_id) as conn:
        # Pesajes del día
        stats = await conn.fetchrow(
            """
            SELECT
                COUNT(*) FILTER (WHERE DATE(registrado_en AT TIME ZONE 'America/Lima') = CURRENT_DATE)
                    AS pesajes_hoy,
                COALESCE(SUM(peso_kg) FILTER (
                    WHERE tipo='entrada'
                    AND DATE(registrado_en AT TIME ZONE 'America/Lima') = CURRENT_DATE
                    AND NOT anulado
                ), 0) AS kg_hoy,
                COUNT(DISTINCT proveedor_id) AS proveedores_activos,
                COUNT(DISTINCT material_id) FILTER (WHERE NOT anulado) AS materiales_en_uso
            FROM pesajes
            WHERE empresa_id = $1
            """,
            empresa_id,
        )

        # Últimas 8 transacciones
        last_txs = await conn.fetch(
            """
            SELECT p.id, m.nombre AS material, m.emoji, pr.nombre AS proveedor,
                   p.peso_kg, p.tipo, p.registrado_en, p.anulado, p.modificado
            FROM pesajes p
            JOIN materiales m ON m.id = p.material_id
            JOIN proveedores pr ON pr.id = p.proveedor_id
            WHERE p.empresa_id = $1
            ORDER BY p.registrado_en DESC
            LIMIT 8
            """,
            empresa_id,
        )

        # Stock total
        stock_total = await conn.fetchval(
            "SELECT COALESCE(SUM(stock_kg),0) FROM inventario WHERE empresa_id=$1",
            empresa_id,
        )

        # Top materiales por ingreso (semana)
        top_mats = await conn.fetch(
            """
            SELECT m.nombre, m.emoji,
                   COALESCE(SUM(p.peso_kg) FILTER (WHERE p.tipo='entrada' AND NOT p.anulado), 0) AS kg
            FROM materiales m
            LEFT JOIN pesajes p ON p.material_id = m.id
                AND p.registrado_en >= NOW() - INTERVAL '7 days'
                AND p.empresa_id = $1
            WHERE m.empresa_id = $1
            GROUP BY m.id, m.nombre, m.emoji
            HAVING COALESCE(SUM(p.peso_kg) FILTER (WHERE p.tipo='entrada' AND NOT p.anulado), 0) > 0
            ORDER BY kg DESC
            LIMIT 6
            """,
            empresa_id,
        )

        # Inventario resumen (top 6)
        inv_summary = await conn.fetch(
            """
            SELECT m.nombre, m.emoji, m.codigo,
                   cat.nombre AS categoria,
                   i.stock_kg,
                   (SELECT COALESCE(SUM(stock_kg),1) FROM inventario WHERE empresa_id=$1) AS total
            FROM inventario i
            JOIN materiales m ON m.id = i.material_id
            LEFT JOIN categorias_material cat ON cat.id = m.categoria_id
            WHERE i.empresa_id = $1 AND i.stock_kg > 0
            ORDER BY i.stock_kg DESC
            LIMIT 6
            """,
            empresa_id,
        )

    def row2dict(r):
        d = dict(r)
        for k, v in d.items():
            if hasattr(v, 'isoformat'):
                d[k] = v.isoformat()
            elif hasattr(v, '__str__') and type(v).__name__ == 'UUID':
                d[k] = str(v)
        return d

    return {
        "stats": {
            "pesajes_hoy": stats["pesajes_hoy"],
            "kg_hoy": float(stats["kg_hoy"]),
            "proveedores_activos": stats["proveedores_activos"],
            "materiales_en_uso": stats["materiales_en_uso"],
            "stock_total": float(stock_total),
            "total_transacciones": stats["pesajes_hoy"],
        },
        "last_transactions": [row2dict(r) for r in last_txs],
        "chart_data": [
            {"nombre": r["nombre"], "emoji": r["emoji"], "kg": float(r["kg"])}
            for r in top_mats
        ],
        "inv_summary": [
            {
                "nombre": r["nombre"],
                "emoji": r["emoji"],
                "codigo": r["codigo"],
                "categoria": r["categoria"],
                "stock_kg": float(r["stock_kg"]),
                "pct": round(float(r["stock_kg"]) / float(r["total"]) * 100, 1) if r["total"] else 0,
            }
            for r in inv_summary
        ],
    }
