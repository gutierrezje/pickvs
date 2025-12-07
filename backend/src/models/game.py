from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class OddsResponse(BaseModel):
    """Single market odds response model."""

    market_type: str
    home_odds: float
    away_odds: float
    line_value: float | None = None


class GameWithOdds(BaseModel):
    game_id: UUID
    home_team: str
    away_team: str
    game_timestamp: datetime
    status: str
    odds: list[OddsResponse] = Field(default_factory=list)


class UpcomingGamesResponse(BaseModel):
    """List of upcoming games."""

    games: list[GameWithOdds] = Field(default_factory=list)
