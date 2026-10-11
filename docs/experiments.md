# Experimental Method

Run the complete benchmark suite with:

```bash
python scripts/run_benchmarks.py
```

The runner loads all three committed datasets, validates them, builds one Haversine matrix per dataset, applies common round-trip constraints, and writes `benchmark_results/benchmark_summary.csv` plus `benchmark_results/benchmark_results.json`.

## Datasets

- Small: six total locations, suitable for the exact Brute Force benchmark.
- Medium: thirteen total locations for heuristic comparison.
- Large: twenty-five total locations for scaling behavior.

Brute Force is included only when the number of destinations is at or below the safety limit (default eight in the runner). On larger datasets, no global optimum or optimality gap is claimed.

## Measures

- Route distance in kilometres.
- High-resolution in-process runtime.
- Improvement versus Nearest Neighbor: `(initial - optimized) / initial × 100`.
- Optimality gap, only when an exact result exists: `(heuristic - optimum) / optimum × 100`.
- Algorithm-specific work counts.
- Simulated Annealing distance and runtime for seeds 11, 22, 33, 44, and 55.

Zero-distance baselines and optima are handled explicitly. Runtime varies with machine, Python version, operating system, dataset, and background load. The JSON output records environment details and parameters to support reproduction. Results are generated, never hand-authored.
