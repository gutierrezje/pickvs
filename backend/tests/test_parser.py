from pathlib import Path

from data.parser import parse_csv
from data.types import GameRecord, GameStatus, MarketType, OddsRecord


def test_parse_csv():
    csv_path = Path(__file__).parent.parent / "data" / "oddsData.csv"

    games, odds = parse_csv(csv_path)

    assert len(games) > 0, "No game records parsed"
    assert len(odds) == len(games) * 3, "Odds records count mismatch"

    first_game = games[0]
    assert isinstance(first_game, GameRecord), "First game is not a GameRecord instance"
    assert first_game.status in GameStatus, "Invalid game status"
    assert first_game.home_score is not None, (
        "Home score should not be None for finished games"
    )
    assert first_game.away_score is not None, (
        "Away score should not be None for finished games"
    )

    print(
        f"\nSample Game: {first_game.api_game_id}\n {first_game.home_team} vs {first_game.away_team}\n Score: {first_game.home_score}-{first_game.away_score}"
    )
    print("Sample Odds for first game:")
    for odd in odds[:3]:
        assert isinstance(odd, OddsRecord), "Odds record is not an OddsRecord instance"
        assert odd.market_type in MarketType, "Invalid market type"
        if odd.api_game_id == first_game.api_game_id:
            print(
                f" Market: {odd.market_type}, Home Odds: {odd.home_odds}, Away Odds: {odd.away_odds}"
            )
