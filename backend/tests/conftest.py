"""Pytest configuration and shared fixtures."""

from contextlib import asynccontextmanager

import asyncpg
import pytest
from starlette.testclient import TestClient

from database import get_db
from src.main import app

# Test database URL - hardcoded for test environment
TEST_DATABASE_URL = "postgresql://test_user:test_password@localhost:5433/pickvs_test"


@asynccontextmanager
async def test_lifespan(app):
    """Empty lifespan for tests - we don't need the production db pool."""
    yield


@pytest.fixture(scope="session")
def test_db_url():
    """Get test database URL."""
    return TEST_DATABASE_URL


@pytest.fixture
async def db_connection(test_db_url):
    """Provide a database connection for each test with transaction rollback."""
    conn = await asyncpg.connect(test_db_url)
    transaction = conn.transaction()
    await transaction.start()

    yield conn

    await transaction.rollback()
    await conn.close()


@pytest.fixture
async def clean_tables(test_db_url):
    """Clean tables before each test for isolation."""
    conn = await asyncpg.connect(test_db_url)
    try:
        await conn.execute("TRUNCATE Users, Picks, Odds, Games CASCADE")
    finally:
        await conn.close()


@pytest.fixture
def client(test_db_url, clean_tables) -> TestClient:  # noqa: ARG001
    """FastAPI test client with dependency override for database."""

    async def override_get_db():
        conn = await asyncpg.connect(test_db_url)
        try:
            yield conn
        finally:
            await conn.close()

    app.dependency_overrides[get_db] = override_get_db
    original_lifespan = app.router.lifespan_context
    app.router.lifespan_context = test_lifespan

    try:
        with TestClient(app, raise_server_exceptions=False) as test_client:
            yield test_client
    finally:
        app.router.lifespan_context = original_lifespan
        app.dependency_overrides.clear()
