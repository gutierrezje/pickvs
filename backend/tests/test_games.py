import pytest

from data.records import GameStatus


def get_api_game_id(game_dict, game_id_map):
    """Get api_game_id from game response using game_id_map."""
    for api_id, db_id in game_id_map.items():
        if str(db_id) == game_dict["game_id"]:
            return api_id
    return None


def assert_game_matches(game_dict, sample_game):
    """Assert game response matches expected sample game."""
    assert game_dict["home_team"] == sample_game.home_team
    assert game_dict["away_team"] == sample_game.away_team
    assert game_dict["status"] == sample_game.status.value


def assert_odds_match(actual_odd, expected_odd):
    """Assert odd response matches expected odd with floating-point tolerance."""
    assert float(actual_odd["home_odds"]) == pytest.approx(
        expected_odd.home_odds, abs=0.01
    )
    assert float(actual_odd["away_odds"]) == pytest.approx(
        expected_odd.away_odds, abs=0.01
    )

    if expected_odd.line_value is not None:
        assert float(actual_odd["line_value"]) == pytest.approx(
            expected_odd.line_value, abs=0.01
        )
    else:
        assert actual_odd["line_value"] is None


@pytest.mark.asyncio
async def test_upcoming_games_no_auth(client):
    """Fetch upcoming games while logged out should be unauthorized."""
    response = client.get("/games/upcoming")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_upcoming_games_valid_response(logged_in_client, populated_db):
    """Fetch upcoming games response for tests."""
    assert populated_db is not None
    assert len(populated_db) > 0

    response = logged_in_client.get("/games/upcoming")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_upcoming_games_expected(
    logged_in_client, populated_db, sample_mixed_games_and_odds
):
    """Fetch upcoming games and verify only Scheduled games are returned."""
    sample_games, sample_odds = sample_mixed_games_and_odds

    # Filter to only Scheduled games (endpoint should filter out Finished)

    scheduled_games = [g for g in sample_games if g.status == GameStatus.SCHEDULED]

    response = logged_in_client.get("/games/upcoming")
    assert response.status_code == 200

    data = response.json()
    assert "games" in data

    games = data["games"]
    # Should only return Scheduled games, not Finished
    assert len(games) == len(scheduled_games), (
        f"Expected {len(scheduled_games)} scheduled games, got {len(games)}"
    )

    for game in games:
        # Verify all returned games are Scheduled
        assert game["status"] == "Scheduled", (
            f"Game {game['game_id']} has status {game['status']}"
        )

        # Map response game to sample game
        api_game_id = get_api_game_id(game, populated_db)
        assert api_game_id is not None, (
            f"Game ID {game['game_id']} not found in game_id_map"
        )

        sample_game = next(g for g in sample_games if g.api_game_id == api_game_id)
        assert_game_matches(game, sample_game)

        # Verify all expected odds are present
        expected_odds = [o for o in sample_odds if o.api_game_id == api_game_id]
        assert len(game["odds"]) == len(expected_odds)

        for odd in game["odds"]:
            matching_odd = next(
                (o for o in expected_odds if o.market_type.value == odd["market_type"]),
                None,
            )
            assert matching_odd is not None, (
                f"Unexpected market_type: {odd['market_type']}"
            )
            assert_odds_match(odd, matching_odd)
