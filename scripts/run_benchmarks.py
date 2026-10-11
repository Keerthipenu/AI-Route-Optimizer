from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data_loader import SAMPLE_FILES, load_sample
from src.distance import build_distance_matrix
from src.evaluation import evaluate_algorithms, repeated_annealing
from src.models import RouteConstraints
from src.validation import frame_to_locations


def main() -> None:
    parser = argparse.ArgumentParser(description="Run reproducible ROUTEFORGE benchmarks.")
    parser.add_argument("--iterations", type=int, default=3000)
    parser.add_argument("--seeds", default="11,22,33,44,55")
    parser.add_argument("--output", type=Path, default=ROOT / "benchmark_results")
    args = parser.parse_args()
    seeds = [int(item) for item in args.seeds.split(",")]
    args.output.mkdir(parents=True, exist_ok=True)
    payload: dict[str, object] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "parameters": {"iterations": args.iterations, "seeds": seeds},
        "datasets": {},
    }
    combined_rows: list[dict[str, object]] = []
    for dataset_name in SAMPLE_FILES:
        frame = load_sample(dataset_name)
        locations = frame_to_locations(frame)
        matrix = build_distance_matrix(locations)
        constraints = RouteConstraints()
        report = evaluate_algorithms(
            matrix, constraints, seed=seeds[0], sa_iterations=args.iterations, brute_force_limit=8
        )
        repeats = repeated_annealing(matrix, constraints, seeds, args.iterations)
        table = report.table.copy()
        table.insert(0, "Dataset", dataset_name)
        combined_rows.extend(table.where(table.notna(), None).to_dict(orient="records"))
        payload["datasets"][dataset_name] = {
            "locations": len(locations),
            "comparison": report.table.where(report.table.notna(), None).to_dict(orient="records"),
            "annealing_runs": repeats.to_dict(orient="records"),
            "environment": report.metadata,
        }
    import pandas as pd

    pd.DataFrame(combined_rows).to_csv(args.output / "benchmark_summary.csv", index=False)
    (args.output / "benchmark_results.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {args.output / 'benchmark_summary.csv'}")
    print(f"Wrote {args.output / 'benchmark_results.json'}")


if __name__ == "__main__":
    main()
