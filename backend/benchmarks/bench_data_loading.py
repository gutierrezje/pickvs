"""Benchmarks for data loading.

Run benchmarks:
    pixi run benchmark              # Optimized approach (20% of data)
    pixi run benchmark-single       # Single-insert approach (20% of data)
    pixi run benchmark-all          # Compare both approaches
"""

import pytest

from data.load import insert_game, insert_games, insert_odd, insert_odds
from data.parser import parse_csv


def create_subset(games, odds, fraction: float):
    """Create a subset of games and odds for benchmarking."""
    if fraction >= 1.0:
        return games, odds

    subset_size = int(len(games) * fraction)
    subset_games = games[:subset_size]

    subset_game_ids = {game.api_game_id for game in subset_games}
    subset_odds = [odd for odd in odds if odd.api_game_id in subset_game_ids]

    return subset_games, subset_odds


@pytest.fixture(scope="module")
def parsed_data(csv_path):
    """Parse CSV once and cache for all benchmark tests."""
    return parse_csv(csv_path)


@pytest.fixture(scope="module")
def subset_data(parsed_data):
    """Create 20% subset for benchmarking."""
    games, odds = parsed_data
    return create_subset(games, odds, 0.75)


@pytest.mark.asyncio
async def test_bench_optimized(benchmark, benchmark_db, subset_data):
    """Benchmark optimized approach with transaction + executemany.

    Uses transaction wrapper + executemany for odds batching.
    Extrapolate results by 5x to estimate full dataset performance.
    """
    subset_games, subset_odds = subset_data
    print(f"\nOptimized: {len(subset_games):,} games, {len(subset_odds):,} odds (20%)")

    async def run_load():
        async with benchmark_db.transaction():
            game_id_map = await insert_games(benchmark_db, subset_games)
            await insert_odds(benchmark_db, subset_odds, game_id_map)

    await benchmark.pedantic(run_load, rounds=1, iterations=1)


@pytest.mark.asyncio
async def test_bench_single_inserts(benchmark, benchmark_db, subset_data):
    """Benchmark single-insert approach (transaction per insert).

    Uses individual transactions for each insert to simulate worst-case scenario.
    This represents the original unoptimized approach where each insert commits.
    """
    subset_games, subset_odds = subset_data
    print(
        f"\nSingle-insert: {len(subset_games):,} games, {len(subset_odds):,} odds (20%)"
    )

    async def run_load():
        # Wrap each insert in its own transaction to force individual commits
        game_id_map = {}

        for game in subset_games:
            async with benchmark_db.transaction():
                game_id = await insert_game(benchmark_db, game)
                game_id_map[game.api_game_id] = game_id

        for odd in subset_odds:
            game_id = game_id_map.get(odd.api_game_id)
            if game_id:
                async with benchmark_db.transaction():
                    await insert_odd(benchmark_db, odd, game_id)

    await benchmark.pedantic(run_load, rounds=1, iterations=1)
