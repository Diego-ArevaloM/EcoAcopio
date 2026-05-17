# EcoAcopio ERP

Sistema de Gestión para Centros de Acopio y Reciclaje — ODS 8, 9, 12

---

## Estructura del Proyecto

```
ecoacopio/
├── schema.sql                  ← Script SQL para crear la BD (ejecutar primero)
├── README.md
│
├── backend/
│   ├── main.py                 ← Punto de entrada FastAPI
│   ├── requirements.txt
│   ├── .env.example            ← Plantilla de variables de entorno
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           ← Variables de entorno (DATABASE_URL, JWT, etc.)
│   │   ├── database.py         ← Pool asyncpg + RLS helper
│   │   └── auth.py             ← JWT, bcrypt, dependencias FastAPI
│   │
│   └── routers/
│       ├── __init__.py
│       ├── auth.py             ← Login, logout, register, change-password
│       ├── dashboard.py        ← Stats del día, últimas transacciones
│       ├── pesajes.py          ← CRUD de pesajes (RN-01, 03, 04, 06)
│       ├── materiales.py       ← Lista maestra (RN-07)
│       ├── proveedores.py      ← Proveedores (RN-08, 09)
│       ├── inventario.py       ← Stock en tiempo real (RN-05)
│       ├── reportes.py         ← Cierres mensuales + CSV (RN-13)
│       ├── auditoria.py        ← Log inmutable (RN-12)
│       └── scanner.py          ← Proxy seguro a Anthropic IA
│
└── frontend/                   ← Interfaz de Usuario (SPA)
    ├── src/
    │   ├── components/         ← Componentes UI reutilizables
    │   │   └── Modal.jsx
    │   ├── hooks/              ← Custom hooks de estado y lógica
    │   │   ├── useClock.jsx
    │   │   └── useToast.jsx
    │   ├── pages/              ← Vistas/Pantallas del sistema
    │   │   ├── Auditoria.jsx
    │   │   ├── Dashboard.jsx
    │   │   ├── Inventario.jsx
    │   │   ├── Login.jsx
    │   │   ├── Materiales.jsx
    │   │   ├── Pesaje.jsx
    │   │   ├── Proveedores.jsx
    │   │   ├── Reportes.jsx
    │   │   └── Scanner.jsx
    │   ├── services/           ← Lógica de conexión HTTP con el backend
    │   │   └── api.js
    │   ├── App.jsx             ← Enrutador principal y estructura base (Layout)
    │   ├── index.css           ← Hoja de estilos globales (Diseño UI)
    │   └── main.jsx            ← Punto de montaje de React
    │
    ├── index.html              ← Punto de entrada HTML
    ├── package.json            ← Dependencias y scripts de Node.js
    └── vite.config.js          ← Configuración del empaquetador Vite
```

---

## Paso 1 — Preparar la Base de Datos (Neon)

1. Entra a [neon.tech](https://neon.tech) y crea un proyecto (o usa uno existente).
2. Copia la **Connection String** (formato `postgresql://...`).
3. En el panel SQL de Neon (o cualquier cliente PostgreSQL), **ejecuta todo el contenido de `schema.sql`**.

   Esto crea:
   - Todas las tablas con sus constraints
   - Triggers para actualizar inventario automáticamente (RN-05, RN-06)
   - Row Level Security (RLS) por empresa
   - Empresa demo + usuarios iniciales + materiales de prueba

   **Usuarios creados por el schema:**

   | Email | Contraseña | Rol |
   |---|---|---|
   | admin@ecoacopio.pe | admin1234 | admin |
   | operario@ecoacopio.pe | operario1234 | operario |

   > ⚠️ Cambia estas contraseñas en producción usando el endpoint `PUT /api/auth/change-password`.

---

## Paso 2 — Configurar el Backend

```bash
cd backend

# Copiar y editar variables de entorno
cp .env.example .env
# Editar .env con tu editor favorito
```

Contenido mínimo del `.env`:

```env
DATABASE_URL=postgresql://usuario:pass@ep-xxxx.us-east-2.aws.neon.tech/ecoacopio?sslmode=require
SECRET_KEY=genera_con__python_-c_"import_secrets;print(secrets.token_hex(32))"
ANTHROPIC_API_KEY=sk-ant-api03-...   # Opcional, para el Scanner IA
```

Generar un `SECRET_KEY` seguro:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Paso 3 — Instalar Dependencias y Ejecutar

```bash
cd backend

# Crear entorno virtual (recomendado)
python -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar el servidor
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

El backend estará disponible en: `http://localhost:8000`

Documentación automática de la API: `http://localhost:8000/docs`

---

## Paso 4 — Servir el Frontend

cd frontend

# 1. Instalar dependencias de Node
npm install

# 2. Levantar el servidor de desarrollo Frontend
npm run dev


## Despliegue en Producción

### Railway / Render / Fly.io

1. Sube el proyecto a GitHub.
2. En la plataforma de despliegue, configura:
   - **Root directory:** `backend`
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
3. Agrega las variables de entorno desde tu `.env`.
4. Para Railway/Render, asegúrate de incluir `frontend/` también en el repositorio.

### Variables de entorno requeridas en producción

```
DATABASE_URL        ← Connection string de Neon
SECRET_KEY          ← String aleatorio de 64+ caracteres
ANTHROPIC_API_KEY   ← Tu API key de Anthropic
ACCESS_TOKEN_EXPIRE_MINUTES=480
LIMITE_PESO_ALERTA_KG=5000
```

### CORS en producción

En `main.py`, reemplaza `allow_origins=["*"]` por tu dominio real:

```python
allow_origins=["https://tudominio.com"],
```

---

## Endpoints de la API

| Método | Ruta | Descripción | Rol |
|---|---|---|---|
| POST | `/api/auth/login` | Iniciar sesión | Público |
| POST | `/api/auth/logout` | Cerrar sesión | Autenticado |
| GET | `/api/auth/me` | Datos del usuario actual | Autenticado |
| POST | `/api/auth/register` | Crear usuario | Admin |
| PUT | `/api/auth/change-password` | Cambiar contraseña | Autenticado |
| GET | `/api/dashboard/stats` | Estadísticas del día | Autenticado |
| GET | `/api/pesajes/` | Listar pesajes | Autenticado |
| POST | `/api/pesajes/` | Crear pesaje | Autenticado |
| PUT | `/api/pesajes/{id}/anular` | Anular pesaje | Admin |
| GET | `/api/materiales/` | Listar materiales | Autenticado |
| POST | `/api/materiales/` | Crear material | Admin |
| PUT | `/api/materiales/{id}` | Actualizar material | Admin |
| PATCH | `/api/materiales/{id}/toggle` | Activar/desactivar | Admin |
| GET | `/api/proveedores/` | Listar proveedores | Autenticado |
| POST | `/api/proveedores/` | Crear proveedor | Autenticado |
| PUT | `/api/proveedores/{id}` | Actualizar proveedor | Autenticado |
| DELETE | `/api/proveedores/{id}` | Desactivar proveedor | Admin |
| GET | `/api/inventario/` | Stock en tiempo real | Autenticado |
| GET | `/api/inventario/stock/{id}` | Stock de un material | Autenticado |
| GET | `/api/reportes/` | Reporte mensual | Admin |
| POST | `/api/reportes/cerrar` | Cerrar período | Admin |
| GET | `/api/reportes/exportar-csv` | Exportar CSV | Admin |
| GET | `/api/auditoria/` | Log de auditoría | Admin |
| POST | `/api/scanner/analizar` | Scanner IA | Autenticado |

---

## Reglas de Negocio Implementadas

| Código | Descripción |
|---|---|
| RN-01 | El peso de todo pesaje debe ser mayor a cero |
| RN-03 | La fecha/hora la asigna el servidor (no el cliente) |
| RN-04 | Alerta cuando el peso supera los 5,000 kg (configurable) |
| RN-05 | El inventario se actualiza automáticamente vía trigger SQL |
| RN-06 | El stock nunca puede quedar negativo (trigger SQL) |
| RN-07 | Solo el Admin puede crear/editar/desactivar materiales |
| RN-08 | El número de documento de proveedor es único por empresa |
| RN-09 | El proveedor "Reciclador Anónimo" es inmodificable |
| RN-10 | Solo el Admin accede a Reportes, Materiales y Auditoría |
| RN-12 | Todo cambio de Admin queda en el log de auditoría inmutable |
| RN-13 | Los cierres mensuales son inmutables una vez cerrados |

---

## Solución de Problemas

**Error: `MODULE_NOT_FOUND` o `ModuleNotFoundError: No module named 'core'`**
→ Ejecuta `uvicorn` desde dentro de la carpeta `backend/`, no desde la raíz.

**Error: `asyncpg.exceptions.InvalidCatalogNameError`**
→ Verifica que el `DATABASE_URL` en tu `.env` sea correcto y que la BD exista en Neon.

**Error 401 en todas las rutas**
→ El token JWT expiró o es inválido. Cierra sesión y vuelve a ingresar.

**El Scanner IA devuelve 503**
→ Falta configurar `ANTHROPIC_API_KEY` en el `.env`.

**Stock negativo al anular pesajes**
→ El trigger SQL en Neon protege esto. Si ocurre, revisa que el schema se ejecutó correctamente.
