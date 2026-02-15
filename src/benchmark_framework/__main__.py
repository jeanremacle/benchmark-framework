"""CLI entry point for the benchmark framework.

Usage:
    python -m benchmark_framework <config_dir>

Executes all pending runs and generates a comparison report.
"""

from __future__ import annotations

import sys
from pathlib import Path

from .api import execute_run, generate_report, load_runs


def main() -> None:
    """Run all pending benchmarks and generate a report."""
    if len(sys.argv) < 2:
        print("Usage: python -m benchmark_framework <config_dir>")
        sys.exit(1)

    config_dir = Path(sys.argv[1])
    if not config_dir.is_dir():
        print(f"Error: '{config_dir}' is not a directory")
        sys.exit(1)

    runs_config = load_runs(config_dir / "runs.json")

    pending_runs = [r for r in runs_config.runs if r.status == "pending"]
    if not pending_runs:
        print("No pending runs found.")
    else:
        for run_def in pending_runs:
            print(f"Executing run: {run_def.name} ({run_def.id})")
            results = execute_run(run_id=run_def.id, config_dir=config_dir)
            print(f"  Completed: {len(results)} measurements")

    report_path = config_dir / "comparison_report.md"
    report = generate_report(config_dir=config_dir, output_path=report_path)
    print(f"\nReport written to: {report_path}")
    print("\n" + report)


if __name__ == "__main__":
    main()
