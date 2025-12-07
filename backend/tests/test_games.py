import pytest

@pytest.mark.asyncio
async def test_upcoming_games_valid_response(logged_in_client, populated_db):
    """Fetch upcoming games response for tests."""
    # populated_db is already resolved by pytest, no await needed
    assert populated_db is not None
    assert len(populated_db) > 0  # Verify we have game IDs

    response = logged_in_client.get("/games/upcoming")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_upcoming_games_expected(logged_in_client, populated_db, sample_upcoming_games_and_odds):
    """Fetch upcoming games and verify against sample data."""
    sample_games, sample_odds = sample_upcoming_games_and_odds
    game_id_map = populated_db  # populated_db is already resolved by pytest

    response = logged_in_client.get("/games/upcoming")
    assert response.status_code == 200

    data = response.json()
    assert "games" in data
    games = data["games"]
    assert len(games) == len(sample_games)

    for game in games:
        api_game_id = None
        for k, v in game_id_map.items():
            if str(v) == game["game_id"]:
                api_game_id = k
                break
        assert api_game_id is not None, f"Game ID {game['game_id']} not found in game_id_map"

        sample_game = next(g for g in sample_games if g.api_game_id == api_game_id)
        assert game["home_team"] == sample_game.home_team
        assert game["away_team"] == sample_game.away_team
        assert game["status"] == sample_game.status.value
        # Scheduled games should not have scores
        assert game["status"] == "Scheduled"

        # Verify odds
        odds = game["odds"]
        expected_odds = [o for o in sample_odds if o.api_game_id == api_game_id]
        assert len(odds) == len(expected_odds), f"Expected {len(expected_odds)} odds, got {len(odds)}"
        for odd in odds:
            matching_odd = next(
                (eo for eo in expected_odds if eo.market_type.value == odd["market_type"]), None
            )
            assert matching_odd is not None, f"No matching odd for market_type {odd['market_type']}"
            # Use pytest.approx for floating-point comparison (database DECIMAL precision)
            assert float(odd["home_odds"]) == pytest.approx(matching_odd.home_odds, abs=0.01)
            assert float(odd["away_odds"]) == pytest.approx(matching_odd.away_odds, abs=0.01)
            if matching_odd.line_value is not None:
                assert float(odd["line_value"]) == pytest.approx(matching_odd.line_value, abs=0.01)
            else:
                assert odd["line_value"] is None