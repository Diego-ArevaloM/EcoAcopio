"""
Router del Escáner IA — proxy seguro a Anthropic API para análisis de reciclabilidad.
La API key se guarda en el servidor, nunca se expone al frontend.
"""
import base64
import httpx
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import Optional

from core.config import ANTHROPIC_API_KEY
from core.auth import get_current_user

router = APIRouter()

SYSTEM_PROMPT = """Eres un experto en reciclaje para centros de acopio en Perú. 
Tu ÚNICO propósito es analizar si un objeto es reciclable o no.
Responde SOLO en JSON válido con este formato exacto, sin markdown ni backticks:
{
  "reciclable": true o false,
  "confianza": "Alta" o "Media" o "Baja",
  "material": "Nombre del material identificado",
  "categoria": "Plástico" o "Papel/Cartón" o "Metales" o "Vidrio" o "Electrónico" o "Otro",
  "codigo_material": "PET-01" o "HDPE-01" o "ALU-01" etc. (código del material más cercano),
  "valor_referencial": "S/.X.XX/kg",
  "instrucciones": "Cómo preparar el material para reciclaje (si aplica)",
  "motivo": "Por qué es o no reciclable en 1-2 oraciones claras"
}"""


@router.post("/analizar")
async def analizar_material(
    descripcion: Optional[str] = Form(None),
    imagen: Optional[UploadFile] = File(None),
    current_user: dict = Depends(get_current_user),
):
    if not descripcion and not imagen:
        raise HTTPException(status_code=422, detail="Debes proveer una descripción o imagen")

    if not ANTHROPIC_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="ANTHROPIC_API_KEY no configurada en el servidor. Contáctese con el administrador.",
        )

    # Construir contenido para la API
    user_content = []
    if descripcion:
        user_content.append({"type": "text", "text": f"Analiza este objeto: {descripcion}"})
    if imagen:
        img_bytes = await imagen.read()
        b64 = base64.b64encode(img_bytes).decode()
        media_type = imagen.content_type or "image/jpeg"
        user_content.append({
            "type": "image",
            "source": {"type": "base64", "media_type": media_type, "data": b64},
        })
        if not descripcion:
            user_content.append({"type": "text", "text": "Analiza si este objeto en la imagen es reciclable."})

    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 800,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": user_content}],
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json=payload,
        )

    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Error al consultar la IA")

    data = resp.json()
    raw = "".join(c.get("text", "") for c in data.get("content", []))
    clean = raw.replace("```json", "").replace("```", "").strip()

    try:
        import json
        result = json.loads(clean)
    except Exception:
        raise HTTPException(status_code=502, detail="La IA devolvió una respuesta inesperada")

    return result
