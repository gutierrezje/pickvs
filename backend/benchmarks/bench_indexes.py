"""Benchmarks for database index performance.

Compare results to measure index performance improvement.
"""

import pytest


@pytest.mark.asyncio
async def bench_query_scheduled_games(benchmark, benchmark_db):
    """Benchmark: Fetch scheduled games ordered by timestamp.

    Without index: Full table scan + sort
    With index (idx_games_status_timestamp): Index scan, no sort needed
    Expected improvement: 10-50x faster
    """

    query = """
        SELECT game_id, home_team, away_team, game_timestamp
        FROM Games
        WHERE status = 'Scheduled'
        ORDER BY game_timestamp
        LIMIT 20;
    """

    async def run_query():
        return await benchmark_db.fetch(query)

    result = await benchmark.pedantic(run_query, rounds=10, iterations=5)
    print(f"\nReturned {len(result)} scheduled games")


@pytest.mark.asyncio
async def bench_query_game_odds(benchmark, benchmark_db):
    """Benchmark: Fetch odds for a specific game.

    Without index: Full table scan of Odds table
    With index (idx_odds_game_market): Direct index lookup
    Expected improvement: 10-100x faster
    """

    # Get a game_id to use in benchmark
    game_id_result = await benchmark_db.fetchval("SELECT game_id FROM Games LIMIT 1")
    if not game_id_result:
        pytest.skip("No games in database")

    query = """
        SELECT market_type, home_odds, away_odds, line_value
        FROM Odds
        WHERE game_id = $1
        ORDER BY market_type;
    """

    async def run_query():
        return await benchmark_db.fetch(query, game_id_result)

    result = await benchmark.pedantic(run_query, rounds=10, iterations=5)
    print(f"\nReturned {len(result)} odds for game")


@pytest.mark.asyncio
async def bench_query_user_picks(benchmark, benchmark_db):
    """Benchmark: Fetch user's recent picks.

    Without index: Full table scan of Picks table
    With index (idx_picks_user_created): Index scan
    Expected improvement: 10-50x faster

    Note: This will return 0 picks until you add test data to Picks table.
    """

    # Using a dummy user_id - in real app this would be authenticated user
    test_user_id = "00000000-0000-0000-0000-000000000001"

    query = """
        SELECT pick_id, game_id, market_picked, outcome_picked, result_units
        FROM Picks
        WHERE user_id = $1
        ORDER BY created_at DESC
        LIMIT 20;
    """

    async def run_query():
        return await benchmark_db.fetch(query, test_user_id)

    result = await benchmark.pedantic(run_query, rounds=10, iterations=5)
    print(f"\nReturned {len(result)} picks for user")


@pytest.mark.asyncio
async def bench_query_explain_scheduled_games(benchmark_db):
    """Show query plan for scheduled games query.

    Run this with pytest -v -s to see output.

    Before indexes: "Seq Scan on games" + "Sort"
    After indexes: "Index Scan using idx_games_status_timestamp"
    """
    query = """
        EXPLAIN ANALYZE
        SELECT game_id, home_team, away_team, game_timestamp
        FROM Games
        WHERE status = 'Scheduled'
        ORDER BY game_timestamp
        LIMIT 20;
    """
    result = await benchmark_db.fetch(query)
    print("\n" + "=" * 60)
    print("QUERY PLAN: Scheduled Games")
    print("=" * 60)
    for row in result:
        print(row[0])
    print("=" * 60)


@pytest.mark.asyncio
async def bench_query_explain_game_odds(benchmark_db):
    """Show query plan for game odds lookup.

    Run this with pytest -v -s to see output.

    Before indexes: "Seq Scan on odds"
    After indexes: "Index Scan using idx_odds_game_market"
    """
    # Get a game_id first
    game_id_result = await benchmark_db.fetchval("SELECT game_id FROM Games LIMIT 1")
    if not game_id_result:
        print("\nNo games in database - skipping query plan")
        return

    query = """
        EXPLAIN ANALYZE
        SELECT market_type, home_odds, away_odds, line_value
        FROM Odds
        WHERE game_id = $1
        ORDER BY market_type;
    """
    result = await benchmark_db.fetch(query, game_id_result)
    print("\n" + "=" * 60)
    print("QUERY PLAN: Game Odds Lookup")
    print("=" * 60)
    for row in result:
        print(row[0])
    print("=" * 60)
