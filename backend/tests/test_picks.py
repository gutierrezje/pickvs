from data.records import GameStatus


def test_submit_pick_success(
    logged_in_client, populated_db, sample_mixed_games_and_odds
):
    """Submit a valid pick successfully."""
    sample_games, _ = sample_mixed_games_and_odds
    # Find a scheduled game
    scheduled_game = next(g for g in sample_games if g.status == GameStatus.SCHEDULED)

    pick_data = {
        "game_id": str(populated_db[scheduled_game.api_game_id]),
        "market_picked": "Moneyline",
        "outcome_picked": scheduled_game.home_team,
        "odds_at_pick": 1.85,
    }
    response = logged_in_client.post(
        "/picks/",
        json=pick_data,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["game_id"] == pick_data["game_id"]
    assert data["market_picked"] == pick_data["market_picked"]
    assert data["outcome_picked"] == pick_data["outcome_picked"]
    assert "pick_id" in data
    assert "created_at" in data
    assert data["result_units"] is None


def test_submit_pick_no_auth(client, populated_db):
    pick_data = {
        "game_id": "00000000-0000-0000-0000-000000000000",
        "market_picked": "Moneyline",
        "outcome_picked": "Team A",
        "odds_at_pick": 1.90,
    }
    response = client.post(
        "/picks/",
        json=pick_data,
    )
    assert response.status_code == 403


def test_submit_pick_invalid_game(logged_in_client, populated_db):
    pick_data = {
        "game_id": "11111111-1111-1111-1111-111111111111",  # Non-existent game_id
        "market_picked": "Moneyline",
        "outcome_picked": "Team A",
        "odds_at_pick": 1.90,
    }
    response = logged_in_client.post(
        "/picks/",
        json=pick_data,
    )
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Game not found."


def test_submit_pick_after_start(
    logged_in_client, populated_db, sample_mixed_games_and_odds
):
    # Find a non-scheduled game (Finished)
    sample_games, _ = sample_mixed_games_and_odds
    finished_game = next(g for g in sample_games if g.status == GameStatus.FINISHED)

    pick_data = {
        "game_id": str(populated_db[finished_game.api_game_id]),
        "market_picked": "Moneyline",
        "outcome_picked": finished_game.home_team,
        "odds_at_pick": 1.85,
    }
    response = logged_in_client.post(
        "/picks/",
        json=pick_data,
    )
    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == "Cannot submit pick for a game after it has started."


def test_submit_pick_duplicate_pick(
    logged_in_client, populated_db, sample_mixed_games_and_odds
):
    # Find a scheduled game
    sample_games, _ = sample_mixed_games_and_odds
    scheduled_game = next(g for g in sample_games if g.status == GameStatus.SCHEDULED)

    pick_data = {
        "game_id": str(populated_db[scheduled_game.api_game_id]),
        "market_picked": "Moneyline",
        "outcome_picked": scheduled_game.home_team,
        "odds_at_pick": 1.85,
    }
    # First submission
    response1 = logged_in_client.post(
        "/picks/",
        json=pick_data,
    )
    assert response1.status_code == 201

    # Second submission (duplicate)
    response2 = logged_in_client.post(
        "/picks/",
        json=pick_data,
    )
    assert response2.status_code == 403
