from datetime import UTC, datetime

from fastapi import APIRouter, status
from fastapi.exceptions import HTTPException

from dependencies import ConnectionDep, CurrentUserDep
from models.pick import PickResponse, PickSubmit

router = APIRouter()


@router.post("/", response_model=PickResponse, status_code=status.HTTP_201_CREATED)
async def submit_pick(
    pick: PickSubmit,
    conn: ConnectionDep,
    user_id: CurrentUserDep,
):
    """Submit a pick for a game (authenticated)."""
    # validate game exists and is scheduled
    game = await conn.fetchrow(
        """
        SELECT status, game_timestamp
        FROM Games
        WHERE game_id = $1
        """,
        pick.game_id,
    )

    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Game not found."
        )

    # Ensure pick is being made before game starts
    if game["status"] != "Scheduled" or datetime.now(UTC) >= game["game_timestamp"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot submit pick for a game after it has started.",
        )

    pick_id = await conn.fetchval(
        """
        INSERT INTO Picks (user_id, game_id, market_picked, outcome_picked, odds_at_pick)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING pick_id
        """,
        user_id,
        pick.game_id,
        pick.market_picked,
        pick.outcome_picked,
        pick.odds_at_pick,
    )

    return PickResponse(
        pick_id=pick_id,
        game_id=pick.game_id,
        market_picked=pick.market_picked,
        outcome_picked=pick.outcome_picked,
        created_at=datetime.now(UTC),
    )
