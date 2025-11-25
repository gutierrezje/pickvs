from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class GameStatus(str, Enum):
    SCHEDULED = "Scheduled"
    FINISHED = "Finished"


@dataclass
class GameRecord:
    api_game_id: str
    home_team: str
    away_team: str
    game_timestamp: datetime
    home_score: int | None
    away_score: int | None
    status: GameStatus
