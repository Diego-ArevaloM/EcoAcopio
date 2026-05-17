"""
Configuración central: base de datos, JWT, settings.
"""
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent.parent / ".env")

# ── DATABASE ─────────────────────────────────────────────────────────────────
DATABASE_URL: str = os.environ["DATABASE_URL"]

# ── JWT ──────────────────────────────────────────────────────────────────────
SECRET_KEY: str   = os.getenv("SECRET_KEY", "CAMBIA_ESTO_EN_PRODUCCION_usa_openssl_rand_hex_32")
ALGORITHM: str    = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))

# ── APP ───────────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
LIMITE_PESO_ALERTA_KG: float = float(os.getenv("LIMITE_PESO_ALERTA_KG", "5000"))
