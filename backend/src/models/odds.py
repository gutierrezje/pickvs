from dataclasses import dataclass
from enum import Enum


def american_to_decimal(american_odds: int) -> float:
    if american_odds > 0:
        return (american_odds / 100) + 1
    else:
        return (100 / abs(american_odds)) + 1


class MarketType(str, Enum):
    MONEYLINE = "moneyline"
    SPREAD = "spread"
    TOTALS = "totals"


@dataclass
class OddsRecord:
    api_game_id: str
    market_type: MarketType
    home_odds: float
    away_odds: float
    line_value: float | None
