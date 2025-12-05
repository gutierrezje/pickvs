"""Internal pydantic models for csv parsing and database loading."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class GameStatus(str, Enum):
    SCHEDULED = "Scheduled"
    FINISHED = "Finished"


class MarketType(str, Enum):
    MONEYLINE = "moneyline"
    SPREAD = "spread"
    TOTAL = "total"


class OddsRecord(BaseModel):
    """Odds information for a single market for a game."""

    api_game_id: str = Field(min_length=1)
    market_type: MarketType
    home_odds: float
    away_odds: float
    line_value: float | None = Field(default=None)


class GameRecord(BaseModel):
    """Information about a single game."""

    api_game_id: str = Field(min_length=1)
    home_team: str = Field(min_length=1)
    away_team: str = Field(min_length=1)
    game_timestamp: datetime
    home_score: int | None = Field(ge=0, default=None)
    away_score: int | None = Field(ge=0, default=None)
    status: GameStatus
