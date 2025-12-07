"""Pytest configuration and shared fixtures."""

from contextlib import asynccontextmanager

import asyncpg
import pytest
from starlette.testclient import TestClient

from database import get_db
from data.parser import parse_csv
from data.load import insert_games, insert_odds
from pathlib import Path
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

@pytest.fixture
def sample_upcoming_games_and_odds():
    """Load some sample games and odds from csv, setting status to Scheduled."""
    from data.records import GameStatus

    csv_path=Path(__file__).parent.parent / "data" / "oddsData.csv"
    games, odds = parse_csv(csv_path)

    # Get unique games by api_game_id (CSV has duplicates for home/away perspectives)
    seen_game_ids = set()
    unique_games = []
    for game in games:
        if game.api_game_id not in seen_game_ids:
            seen_game_ids.add(game.api_game_id)
            unique_games.append(game)

    # Take first 5 unique games
    sample_games = unique_games[:5]

    # Convert games to Scheduled status for testing upcoming endpoint
    for game in sample_games:
        game.status = GameStatus.SCHEDULED
        game.home_score = None
        game.away_score = None

    # Deduplicate odds: same game can have duplicate odds from home/away rows
    sample_game_ids = {game.api_game_id for game in sample_games}
    seen_odds = set()
    sample_odds = []
    for odd in odds:
        if odd.api_game_id in sample_game_ids:
            # Create unique key: game_id + market_type
            odd_key = (odd.api_game_id, odd.market_type)
            if odd_key not in seen_odds:
                seen_odds.add(odd_key)
                sample_odds.append(odd)

    return sample_games, sample_odds


@pytest.fixture
async def populated_db(test_db_url, sample_upcoming_games_and_odds):
    """Populate the test database with sample data."""
    sample_games, sample_odds = sample_upcoming_games_and_odds

    conn = await asyncpg.connect(test_db_url)
    try:
        game_id_map = await insert_games(conn, sample_games)
        await insert_odds(conn, sample_odds, game_id_map)
        yield game_id_map
    finally:
        await conn.close()

@pytest.fixture
def logged_in_client(client):
    """Provide a test client with a logged-in user."""
    user_data = {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "TestPass123!",
    }
    # Register a new user
    register_response = client.post(
        "/auth/register",
        json=user_data,
    )
    assert register_response.status_code == 201
    # Log in the user
    login_response = client.post(
        "/auth/login",
        json=user_data,
    )
    assert login_response.status_code == 200
    token = login_response.json().get("access_token")
    assert token is not None
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client

