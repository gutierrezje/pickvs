import os

import asyncpg

db_pool: asyncpg.Pool | None = None


async def get_db():
    """Get a database connection from the pool.

    If pool is not initialized (e.g., in tests before lifespan runs),
    creates a direct connection using TEST_DATABASE_URL if available.
    """
    if db_pool is not None:
        # Normal case: use the pool
        async with db_pool.acquire() as connection:
            yield connection
    else:
        db_url = os.getenv("TEST_DATABASE_URL")
        conn = await asyncpg.connect(db_url)
        try:
            yield conn
        finally:
            await conn.close()
