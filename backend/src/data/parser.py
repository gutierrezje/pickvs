"""
Parse historical game and odds data into structured records.
"""

import csv
from datetime import datetime
from pathlib import Path

from data.types import GameRecord, GameStatus, MarketType, OddsRecord
from utils.odds import american_to_decimal


def parse_csv(csv_path: str | Path) -> tuple[list[GameRecord], list[OddsRecord]]:
    games: list[GameRecord] = []
    odds: list[OddsRecord] = []

    csv_path = Path(csv_path)

    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    with open(csv_path, newline="") as csvfile:
        reader = csv.DictReader(csvfile)

        if reader.fieldnames is None:
            raise ValueError("CSV file has no header")

        required = {
            "date",
            "team",
            "home/visitor",
            "opponent",
            "score",
            "opponentScore",
            "moneyLine",
            "opponentMoneyLine",
            "total",
            "spread",
        }
        fieldnames = set(reader.fieldnames)

        if not required.issubset(fieldnames):
            raise ValueError(f"CSV missing columns: {required - fieldnames}")

        for row in reader:
            is_home = row["home/visitor"].strip() == "vs"
            # Skip rows with invalid moneyline odds (0 means missing/unavailable data)
            try:
                moneyline_home = (
                    int(row["moneyLine"]) if is_home else int(row["opponentMoneyLine"])
                )
                moneyline_away = (
                    int(row["opponentMoneyLine"]) if is_home else int(row["moneyLine"])
                )
            except (ValueError, TypeError):
                # Skip rows where moneyline can't be parsed as integer
                continue

            if moneyline_home == 0 or moneyline_away == 0:
                continue

            date = datetime.strptime(row["date"], "%Y-%m-%d")
            home_team = row["team"] if is_home else row["opponent"]
            away_team = row["opponent"] if is_home else row["team"]
            home_score = int(row["score"]) if is_home else int(row["opponentScore"])
            away_score = int(row["opponentScore"]) if is_home else int(row["score"])

            game_record = GameRecord(
                api_game_id=f"{date.strftime('%Y%m%d')}_{home_team.replace(' ', '')}_{
                    away_team.replace(' ', '')
                }",
                home_team=home_team,
                away_team=away_team,
                game_timestamp=date,
                home_score=home_score,
                away_score=away_score,
                status=GameStatus.FINISHED,
            )
            games.append(game_record)

            # Parse odds (3 markets: moneyline, spread, totals)
            moneyline_record = OddsRecord(
                api_game_id=game_record.api_game_id,
                market_type=MarketType.MONEYLINE,
                home_odds=american_to_decimal(moneyline_home),
                away_odds=american_to_decimal(moneyline_away),
                line_value=None,
            )

            spread_record = OddsRecord(
                api_game_id=game_record.api_game_id,
                market_type=MarketType.SPREAD,
                home_odds=1.909,
                away_odds=1.909,
                line_value=float(row["spread"]) if is_home else (-float(row["spread"])),
            )

            totals_record = OddsRecord(
                api_game_id=game_record.api_game_id,
                market_type=MarketType.TOTALS,
                home_odds=1.909,
                away_odds=1.909,
                line_value=float(row["total"]),
            )

            odds.append(moneyline_record)
            odds.append(spread_record)
            odds.append(totals_record)

    return games, odds
