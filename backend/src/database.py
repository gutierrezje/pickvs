import asyncpg

db_pool: asyncpg.Pool | None = None

async def get_db():
    """Get a database connection from the pool."""
    if db_pool is None:
        raise RuntimeError("Database pool is not initialized")
    async with db_pool.acquire() as connection:
        yield connection
