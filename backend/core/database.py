"""
Pool de conexiones asyncpg para PostgreSQL / Neon.
"""
import asyncpg
from contextlib import asynccontextmanager
from core.config import DATABASE_URL

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=2,
            max_size=10,
            command_timeout=30,
            ssl="require",
        )
    return _pool


async def close_pool():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


@asynccontextmanager
async def get_conn(empresa_id: str | None = None):
    """
    Entrega una conexión con RLS configurado si se provee empresa_id.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        if empresa_id:
            await conn.execute(
                f"SET app.current_empresa_id = '{empresa_id}'"
            )
        yield conn
