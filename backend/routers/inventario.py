"""
Router de inventario — stock en tiempo real, RN-05.
"""
from fastapi import APIRouter, Depends
from typing import Optional

from core.database import get_conn
from core.auth import get_current_user

router = APIRouter()


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
async def get_inventario(
    buscar: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    empresa_id = current_user["empresa_id"]
    filtro_nombre = f"AND LOWER(m.nombre) LIKE '%{buscar.lower()}%'" if buscar else ""

    async with get_conn(empresa_id) as conn:
        rows = await conn.fetch(
            f"""
            SELECT m.id, m.codigo, m.nombre, m.emoji, m.estado,
                   cat.nombre AS categoria,
                   COALESCE(i.stock_kg, 0) AS stock_kg,
                   COALESCE(i.stock_minimo_kg, 0) AS stock_minimo_kg,
                   i.ultima_entrada, i.ultima_salida,
                   (SELECT COALESCE(SUM(stock_kg),1) FROM inventario WHERE empresa_id=$1) AS total_stock
            FROM materiales m
            LEFT JOIN categorias_material cat ON cat.id = m.categoria_id
            LEFT JOIN inventario i ON i.material_id = m.id AND i.empresa_id = $1
            WHERE m.empresa_id = $1 {filtro_nombre}
            ORDER BY COALESCE(i.stock_kg,0) DESC, m.nombre
            """,
            empresa_id,
        )

        totales = await conn.fetchrow(
            """
            SELECT
                COALESCE(SUM(stock_kg), 0) AS total_kg,
                COUNT(*) FILTER (WHERE stock_kg > 0) AS materiales_con_stock,
                COUNT(*) AS total_materiales
            FROM inventario
            WHERE empresa_id = $1
            """,
            empresa_id,
        )

    items = []
    for r in rows:
        d = _row2dict(r)
        total = float(d.get("total_stock") or 1)
        kg = float(d.get("stock_kg") or 0)
        d["pct_total"] = round(kg / total * 100, 1) if total > 0 else 0
        d["nivel"] = "Alto" if kg > 100 else ("Medio" if kg > 30 else "Bajo")
        items.append(d)

    return {
        "items": items,
        "resumen": {
            "total_kg": float(totales["total_kg"]),
            "materiales_con_stock": totales["materiales_con_stock"],
            "total_materiales": totales["total_materiales"],
        },
    }


@router.get("/stock/{material_id}")
async def get_stock_material(
    material_id: str,
    current_user: dict = Depends(get_current_user),
):
    empresa_id = current_user["empresa_id"]
    async with get_conn(empresa_id) as conn:
        row = await conn.fetchrow(
            """
            SELECT m.nombre, m.emoji, m.codigo, m.precio_referencial,
                   cat.nombre AS categoria,
                   COALESCE(i.stock_kg, 0) AS stock_kg,
                   i.ultima_entrada, i.ultima_salida
            FROM materiales m
            LEFT JOIN categorias_material cat ON cat.id = m.categoria_id
            LEFT JOIN inventario i ON i.material_id = m.id AND i.empresa_id = $1
            WHERE m.id = $2 AND m.empresa_id = $1
            """,
            empresa_id, material_id,
        )
    if not row:
        return {"stock_kg": 0}
    return _row2dict(row)
