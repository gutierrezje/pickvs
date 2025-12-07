from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class PickSubmit(BaseModel):
    """Request to submit a pick."""

    game_id: UUID
    market_picked: str
    outcome_picked: str  # Team name or 'Over'/'Under'
    odds_at_pick: float


class PickResponse(BaseModel):
    """Response for a submitted pick."""

    pick_id: UUID
    game_id: UUID
    market_picked: str
    outcome_picked: str
    created_at: datetime
    result_units: float | None = None
