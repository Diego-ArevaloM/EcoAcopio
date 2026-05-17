"""
EcoAcopio ERP — Backend Principal
FastAPI + PostgreSQL (Neon)
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from routers import auth, dashboard, pesajes, materiales, proveedores, inventario, reportes, auditoria, scanner

app = FastAPI(
    title="EcoAcopio ERP API",
    description="ERP para centros de acopio y reciclaje — ODS 8, 9, 12",
    version="1.0.0",
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Producción: reemplaza con tu dominio
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── ROUTERS ──────────────────────────────────────────────────────────────────
app.include_router(auth.router,        prefix="/api/auth",       tags=["Auth"])
app.include_router(dashboard.router,   prefix="/api/dashboard",  tags=["Dashboard"])
app.include_router(pesajes.router,     prefix="/api/pesajes",    tags=["Pesajes"])
app.include_router(materiales.router,  prefix="/api/materiales", tags=["Materiales"])
app.include_router(proveedores.router, prefix="/api/proveedores",tags=["Proveedores"])
app.include_router(inventario.router,  prefix="/api/inventario", tags=["Inventario"])
app.include_router(reportes.router,    prefix="/api/reportes",   tags=["Reportes"])
app.include_router(auditoria.router,   prefix="/api/auditoria",  tags=["Auditoría"])
app.include_router(scanner.router,     prefix="/api/scanner",    tags=["Scanner IA"])

# ── STATIC FILES (Frontend) ───────────────────────────────────────────────────
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
static_dir   = os.path.join(frontend_dir, "static")

if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", include_in_schema=False)
async def serve_frontend():
    index = os.path.join(frontend_dir, "index.html")
    return FileResponse(index)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "EcoAcopio ERP"}
