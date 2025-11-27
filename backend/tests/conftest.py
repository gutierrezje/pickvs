"""Pytest configuration and shared fixtures."""

import os
from pathlib import Path

import asyncpg
import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client() -> TestClient:
    """FastAPI test client fixture."""
    return TestClient(app)


@pytest.fixture(scope="session")
def test_db_url():
    """Get test database URL from environment."""
    db_url = os.getenv("TEST_DATABASE_URL")
    if not db_url:
        pytest.skip("TEST_DATABASE_URL not set - skipping database tests")
    return db_url


@pytest.fixture(scope="session")
async def setup_test_schema(test_db_url):
    """Initialize test database schema once per test session."""
    conn = await asyncpg.connect(test_db_url)
    try:
        # Read and execute schema
        schema_path = Path(__file__).parent.parent / "sql" / "schema.sql"
        if schema_path.exists():
            schema_sql = schema_path.read_text()
            await conn.execute(schema_sql)
        yield
    finally:
        await conn.close()


@pytest.fixture
async def db_connection(test_db_url, setup_test_schema):
    """Provide a clean database connection for each test.

    Uses transactions that are rolled back after each test,
    ensuring test isolation without manual cleanup.
    """
    conn = await asyncpg.connect(test_db_url)

    # Start transaction (will be rolled back after test)
    transaction = conn.transaction()
    await transaction.start()

    yield conn

    # Rollback transaction (undo all test changes)
    await transaction.rollback()
    await conn.close()
