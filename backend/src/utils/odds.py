"""Utilities for odds conversion and calculations."""


def american_to_decimal(american_odds: int) -> float:
    """Convert American odds to Decimal odds.

    Args:
        american_odds: American odds format (e.g., -110, +150)

    Returns:
        Decimal odds format (e.g., 1.91, 2.50)
    """
    if american_odds > 0:
        return (american_odds / 100) + 1
    else:
        return (100 / abs(american_odds)) + 1
