"""Unit tests for database load functions."""

from datetime import datetime
from decimal import Decimal

import pytest

from data.load import insert_game, insert_odd
from models.game import GameRecord, GameStatus
from models.odds import MarketType, OddsRecord


@pytest.fixture
def sample_game():
    """Provide a sample GameRecord for tests."""
    return GameRecord(
        api_game_id="TEST_20240101_TeamA_TeamB",
        home_team="Team A",
        away_team="Team B",
        game_timestamp=datetime(2024, 1, 1, 19, 0),
        status=GameStatus.FINISHED,
        home_score=100,
        away_score=90,
    )


@pytest.fixture
def sample_odds():
    """Provide a sample OddsRecord for tests."""
    return OddsRecord(
        api_game_id="TEST_20240101_TeamA_TeamB",
        market_type=MarketType.MONEYLINE,
        home_odds=1.91,
        away_odds=1.91,
        line_value=None,
    )


@pytest.mark.asyncio
async def test_insert_game(db_connection, sample_game):
    """Test inserting a game returns a valid UUID."""
    game_id = await insert_game(db_connection, sample_game)

    assert game_id is not None
    assert len(game_id) == 36  # UUID format with dashes


@pytest.mark.asyncio
async def test_insert_odds(db_connection, sample_game, sample_odds):
    """Test inserting odds for a game."""
    # First insert game to get game_id
    game_id = await insert_game(db_connection, sample_game)

    # Then insert odds (should not raise)
    await insert_odd(db_connection, sample_odds, game_id)

    # Verify odds were inserted
    result = await db_connection.fetchrow(
        "SELECT * FROM Odds WHERE game_id = $1::uuid", game_id
    )
    assert result is not None
    assert result["market_type"] == MarketType.MONEYLINE.value
    assert result["home_odds"] == Decimal("1.91")
    assert result["away_odds"] == Decimal("1.91")


@pytest.mark.asyncio
async def test_duplicate_game_insert(db_connection, sample_game):
    """Test inserting the same game twice updates instead of erroring."""
    # First insert
    game_id_1 = await insert_game(db_connection, sample_game)

    # Modify score and insert again
    sample_game.home_score = 125
    game_id_2 = await insert_game(db_connection, sample_game)

    # Should return same game_id
    assert game_id_1 == game_id_2

    # Verify score was updated
    result = await db_connection.fetchrow(
        "SELECT home_score FROM Games WHERE game_id = $1::uuid", game_id_1
    )
    assert result["home_score"] == 125
