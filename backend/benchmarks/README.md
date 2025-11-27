# Benchmarks

Performance benchmarks for database operations and data loading using pytest-benchmark.

## Structure

```
benchmarks/
├── __init__.py
├── conftest.py           # Pytest fixtures for benchmarks
├── bench_data_loading.py # Data loading benchmarks
└── README.md             # This file
```

## Running Benchmarks

### Optimized Approach (Recommended)

```bash
pixi run benchmark
```

Benchmarks the optimized approach with:
- Single transaction wrapper (one commit at end)
- executemany for odds batching (1000 records per call)
- 75% of dataset (~27,800 games, ~83,300 odds)

Expected performance on local database:
- ~290-300 seconds for 75% subset
- ~390-400 seconds for full dataset (extrapolated)

With remote database (Neon), performance improvement vs single-insert is much larger due to network latency.

### Single-Insert Approach (Baseline)

```bash
pixi run benchmark-single
```

Benchmarks the unoptimized single-insert approach with:
- Transaction per insert (~111k individual commits)
- Individual inserts for all records (no batching)
- 75% of dataset (~27,800 games, ~83,300 odds)

Expected performance on local database:
- ~370-380 seconds for 75% subset
- ~28% slower than optimized approach

This represents the worst-case scenario before optimizations were applied.

### Compare Both

```bash
pixi run benchmark-all
```

Runs both benchmarks to compare optimized vs single-insert performance.

## pytest-benchmark Features

- **Statistical analysis**: Mean, stddev, min/max, percentiles
- **Comparison tracking**: Compare runs over time with `--benchmark-compare`
- **JSON export**: Save results for CI/CD with `--benchmark-json=output.json`
- **Auto-calibration**: Automatically determines iterations needed
- **Histogram output**: Visualize performance distribution

## Advanced Usage

### Compare Performance Over Time

Save a baseline benchmark:

```bash
pytest benchmarks/ -v --benchmark-save=baseline
```

Compare against baseline:

```bash
pytest benchmarks/ -v --benchmark-compare=baseline
```

This shows percentage differences and highlights regressions.

### Export Results for CI/CD

```bash
pytest benchmarks/ --benchmark-json=results.json
```

Track performance metrics over commits in your CI pipeline.

### Only Run Benchmarks (Skip Regular Tests)

```bash
pytest benchmarks/ --benchmark-only
```

### Disable Benchmarks (Run as Regular Tests)

```bash
pytest benchmarks/ --benchmark-disable
```

## Best Practices

1. **Use sufficient data volume**: Current benchmarks use 75% of dataset to show meaningful differences
2. **Use real database**: Benchmarks measure actual commit performance (not mocked)
3. **Local vs Remote matters**: Performance differences are more dramatic with network latency (Neon vs Docker)
4. **Track regressions**: Use `--benchmark-compare` to catch slowdowns over time
5. **CI integration**: Save benchmark results in automated tests to monitor performance

## Understanding Results

pytest-benchmark output shows:

- **Min**: Fastest run (best case)
- **Max**: Slowest run (worst case)
- **Mean**: Average time across runs
- **StdDev**: Consistency of performance
- **Median**: Middle value (less affected by outliers)
- **IQR**: Interquartile range (spread of middle 50%)
- **Outliers**: Runs significantly different from others

### Performance Insights

**Local Database (Docker)**:
- Transaction optimization provides ~28% speedup (292s vs 375s)
- Relatively modest because localhost has minimal network latency
- Fast SSD reduces commit overhead

**Remote Database (Neon)**:
- Transaction optimization provides 2-5x speedup or more
- Network latency (10-50ms per commit) dominates performance
- Single transaction = 1 round-trip vs ~111k round-trips for single-insert
- This is where the optimization really shines in production

## Adding New Benchmarks

For database operations:

```python
# benchmarks/bench_my_operation.py
import pytest

@pytest.mark.asyncio
async def test_bench_my_operation(benchmark, benchmark_db):
    async def operation():
        # Your database operation here
        pass

    await benchmark.pedantic(operation, rounds=1, iterations=1)
```

Run with:

```bash
pixi run benchmark-all
```
