"""Pytest configuration for benchmarks."""

import os
from pathlib import Path

import asyncpg
import pytest


@pytest.fixture(scope="session")
def benchmark_db_url():
    """Get benchmark database URL from environment.

    Uses TEST_DATABASE_URL for benchmarks to avoid polluting production data.
    """
    db_url = os.getenv("TEST_DATABASE_URL")
    if not db_url:
        pytest.skip("TEST_DATABASE_URL not set - skipping benchmarks")
    return db_url


@pytest.fixture(scope="session")
async def setup_benchmark_schema(benchmark_db_url):
    """Initialize benchmark database schema once per session."""
    conn = await asyncpg.connect(benchmark_db_url)
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
async def benchmark_db(benchmark_db_url, setup_benchmark_schema):
    """Provide a clean database connection for benchmarks.

    Note: Unlike test fixtures, this does NOT use transactions.
    Benchmarks measure real commit performance.
    You must manually clean up data if needed.
    """
    conn = await asyncpg.connect(benchmark_db_url)
    yield conn
    await conn.close()


@pytest.fixture(scope="module")
def csv_path():
    """Path to the CSV data file for benchmarking."""
    return Path(__file__).parent.parent / "data" / "oddsData.csv"
