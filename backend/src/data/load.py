"""Data loader for importing CSV data into the database."""

import asyncio
import os
from pathlib import Path

import asyncpg

from data.parser import parse_csv
from data.models import GameRecord, OddsRecord


async def get_db_connection(use_pooler: bool = False) -> asyncpg.Connection:
    db_url = os.getenv("DATABASE_URL_POOLER" if use_pooler else "DATABASE_URL")
    if not db_url:
        raise ValueError("Database URL not found in environment variables.")
    return await asyncpg.connect(dsn=db_url)


async def insert_game(conn: asyncpg.Connection, game: GameRecord) -> str:
    """Insert a single game record and return its game_id.

    This is a simple wrapper for testing. For bulk imports, use insert_games().
    """
    query = """
        INSERT INTO Games (api_game_id, home_team, away_team, game_timestamp, status, home_score, away_score)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        ON CONFLICT (api_game_id)
        DO UPDATE SET
            status = EXCLUDED.status,
            home_score = EXCLUDED.home_score,
            away_score = EXCLUDED.away_score,
            fetched_at = NOW()
        RETURNING game_id;
    """
    result = await conn.fetchval(
        query,
        game.api_game_id,
        game.home_team,
        game.away_team,
        game.game_timestamp,
        game.status.value,
        game.home_score,
        game.away_score,
    )
    return str(result)


async def insert_odd(conn: asyncpg.Connection, odds: OddsRecord, game_id: str) -> None:
    """Insert a single odds record.

    This is a simple wrapper for testing. For bulk imports, use insert_odds().
    """
    query = """
        INSERT INTO Odds (game_id, market_type, home_odds, away_odds, line_value)
        VALUES ($1::uuid, $2, $3, $4, $5)
        ON CONFLICT (game_id, market_type)
        DO UPDATE SET
            home_odds = EXCLUDED.home_odds,
            away_odds = EXCLUDED.away_odds,
            line_value = EXCLUDED.line_value;
    """
    await conn.execute(
        query,
        game_id,
        odds.market_type.value,
        odds.home_odds,
        odds.away_odds,
        odds.line_value,
    )


async def insert_games(
    conn: asyncpg.Connection, games: list[GameRecord], batch_size: int = 500
) -> dict[str, str]:
    """Insert games and return mapping of api_game_id -> game_id.

    Uses batch insert with executemany followed by a single SELECT to fetch
    the game_id mappings, reducing database round-trips from N to 2 per batch.

    Args:
        conn: Database connection
        games: List of GameRecord objects to insert
        batch_size: Number of games to insert per batch (default 500)

    Returns:
        Dictionary mapping api_game_id to database game_id (UUID as string)
    """
    game_id_map = {}

    insert_query = """
        INSERT INTO Games (api_game_id, home_team, away_team, game_timestamp, status, home_score, away_score)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        ON CONFLICT (api_game_id)
        DO UPDATE SET
            status = EXCLUDED.status,
            home_score = EXCLUDED.home_score,
            away_score = EXCLUDED.away_score,
            fetched_at = NOW();
    """

    select_query = """
        SELECT api_game_id, game_id FROM Games WHERE api_game_id = ANY($1);
    """

    total = len(games)
    for i in range(0, total, batch_size):
        batch = games[i : i + batch_size]

        # Prepare batch data for executemany
        batch_data = [
            (
                game.api_game_id,
                game.home_team,
                game.away_team,
                game.game_timestamp,
                game.status.value,
                game.home_score,
                game.away_score,
            )
            for game in batch
        ]

        # Batch insert all games
        await conn.executemany(insert_query, batch_data)

        # Fetch all game_id mappings in a single query
        api_game_ids = [game.api_game_id for game in batch]
        results = await conn.fetch(select_query, api_game_ids)

        for row in results:
            game_id_map[row["api_game_id"]] = str(row["game_id"])

        print(f"Inserted {min(i + batch_size, total)}/{total} games...")

    return game_id_map


async def insert_odds(
    conn: asyncpg.Connection,
    odds: list[OddsRecord],
    game_id_map: dict[str, str],
    batch_size: int = 1000,
) -> None:
    """Insert odds records in batches using executemany.

    Args:
        conn: Database connection
        odds: List of OddsRecord objects to insert
        game_id_map: Mapping of api_game_id to database game_id
        batch_size: Number of odds to insert per executemany call (default 1000)
    """
    query = """
        INSERT INTO Odds (game_id, market_type, home_odds, away_odds, line_value)
        VALUES ($1::uuid, $2, $3, $4, $5)
        ON CONFLICT (game_id, market_type)
        DO UPDATE SET
            home_odds = EXCLUDED.home_odds,
            away_odds = EXCLUDED.away_odds,
            line_value = EXCLUDED.line_value;
    """

    total = len(odds)
    for i in range(0, total, batch_size):
        batch = odds[i : i + batch_size]

        # Prepare batch data
        batch_data = [
            (
                game_id_map.get(odd.api_game_id),
                odd.market_type.value,
                odd.home_odds,
                odd.away_odds,
                odd.line_value,
            )
            for odd in batch
            if odd.api_game_id in game_id_map  # Skip if game not found
        ]

        # Execute batch insert using executemany
        await conn.executemany(query, batch_data)

        print(f"Inserted {min(i + batch_size, total)}/{total} odds records...")


async def load_csv_to_db(csv_path: str | Path, use_pooler: bool = False) -> None:
    """Parse CSV and load data into the database using batched inserts."""
    print(f"Loading data from {csv_path}...")
    games, odds = parse_csv(csv_path)
    print(f"Parsed {len(games)} games and {len(odds)} odds records")

    print("Connecting to database...")
    conn = await get_db_connection(use_pooler=use_pooler)

    try:
        # Use transaction for better performance (single commit at end)
        async with conn.transaction():
            print("Inserting games...")
            game_id_map = await insert_games(conn, games)

            print("Inserting odds...")
            await insert_odds(conn, odds, game_id_map)

        print("Transaction committed. Data loading complete!")

    finally:
        await conn.close()
        print("Database connection closed")


if __name__ == "__main__":
    csv_path = Path(__file__).parent.parent.parent / "data" / "oddsData.csv"
    asyncio.run(load_csv_to_db(csv_path, use_pooler=False))
