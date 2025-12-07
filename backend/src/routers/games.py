from models.game import OddsResponse
from models.game import GameWithOdds
from typing import Annotated
from fastapi import APIRouter, Depends
from asyncpg import Connection
from models.game import UpcomingGamesResponse, GameWithOdds
from database import get_db

ConnectionDep = Annotated[Connection, Depends(get_db)]

router = APIRouter()

@router.get("/upcoming", response_model=UpcomingGamesResponse)
async def get_upcoming_games(conn: ConnectionDep, limit: int | None = None):
    """Fetch all scheduled games with odds."""
    query = """
        SELECT game_id, home_team, away_team, game_timestamp, status
        FROM Games
        WHERE status = 'Scheduled'
        ORDER BY game_timestamp
    """
    if limit is not None:
        query += f" LIMIT {limit}"
    
    games = await conn.fetch(query)

    result = []
    for game in games:
        # Fetch odds for this game
        odds = await conn.fetch(
            """
            SELECT market_type, home_odds, away_odds, line_value
            FROM Odds
            WHERE game_id = $1
            ORDER BY market_type
            """,
            game["game_id"]
        )

        game_with_odds = GameWithOdds(
            game_id=game["game_id"],
            home_team=game["home_team"],
            away_team=game["away_team"],
            game_timestamp=game["game_timestamp"],
            status=game["status"],
            odds=[
                OddsResponse(
                    market_type=odd["market_type"],
                    home_odds=odd["home_odds"],
                    away_odds=odd["away_odds"],
                    line_value=odd["line_value"],
                )
                for odd in odds
            ]
        )
        result.append(game_with_odds)

    return UpcomingGamesResponse(games=result)