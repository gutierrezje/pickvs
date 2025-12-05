import asyncpg

db_pool: asyncpg.Pool | None = None


async def get_db():
    """Get a database connection from the pool.

    This dependency is overridden in tests to use a test database connection.
    """
    if db_pool is None:
        raise RuntimeError("Database pool not initialized. Is the app running?")

    async with db_pool.acquire() as connection:
        yield connection
