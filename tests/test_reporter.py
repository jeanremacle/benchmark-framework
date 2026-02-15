"""Tests for BenchmarkReporter."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from benchmark_framework.reporter import BenchmarkReporter


def _setup_config_with_results(tmp_path: Path, fixtures_dir: Path) -> Path:
    """Create a config dir with completed run and results."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    # Copy fixtures
    for name in ["iterations.json", "metrics.json"]:
        shutil.copy(fixtures_dir / name, config_dir / name)

    # Write a completed run
    runs = {
        "runs": [
            {
                "id": "run-001",
                "name": "Baseline benchmark",
                "description": "Compare baseline vs optimized",
                "iteration_ids": ["v1-baseline", "v2-optimized"],
                "metric_ids": ["exec_time"],
                "status": "completed",
                "created_at": "2025-02-14T15:00:00Z",
            }
        ]
    }
    (config_dir / "runs.json").write_text(json.dumps(runs, indent=2))

    # Write results
    results = {
        "results": [
            {
                "run_id": "run-001",
                "iteration_id": "v1-baseline",
                "metric_id": "exec_time",
                "value": 2.5,
                "unit": "seconds",
                "executed_at": "2025-02-14T16:00:00Z",
                "environment": {"platform": "linux"},
                "metadata": {},
            },
            {
                "run_id": "run-001",
                "iteration_id": "v2-optimized",
                "metric_id": "exec_time",
                "value": 1.2,
                "unit": "seconds",
                "executed_at": "2025-02-14T16:01:00Z",
                "environment": {"platform": "linux"},
                "metadata": {},
            },
        ]
    }
    (config_dir / "results.json").write_text(json.dumps(results, indent=2))

    return config_dir


class TestBenchmarkReporter:
    def test_generates_report(self, tmp_path: Path, fixtures_dir: Path) -> None:
        config_dir = _setup_config_with_results(tmp_path, fixtures_dir)
        reporter = BenchmarkReporter(config_dir)
        report = reporter.generate_report()

        assert "Benchmark Comparison Report" in report
        assert "Baseline benchmark" in report
        assert "Execution Time" in report

    def test_highlights_best_value(self, tmp_path: Path, fixtures_dir: Path) -> None:
        config_dir = _setup_config_with_results(tmp_path, fixtures_dir)
        reporter = BenchmarkReporter(config_dir)
        report = reporter.generate_report()

        # exec_time is higher_is_better=false, so 1.2 (v2) is best
        assert "**1.2000**" in report

    def test_includes_narrative(self, tmp_path: Path, fixtures_dir: Path) -> None:
        config_dir = _setup_config_with_results(tmp_path, fixtures_dir)
        reporter = BenchmarkReporter(config_dir)
        report = reporter.generate_report()

        assert "### Analysis" in report
        assert "lowest" in report

    def test_writes_to_file(self, tmp_path: Path, fixtures_dir: Path) -> None:
        config_dir = _setup_config_with_results(tmp_path, fixtures_dir)
        output = tmp_path / "report.md"

        reporter = BenchmarkReporter(config_dir)
        report = reporter.generate_report(output_path=output)

        assert output.exists()
        assert output.read_text() == report

    def test_no_completed_runs(self, tmp_path: Path, fixtures_dir: Path) -> None:
        config_dir = tmp_path / "empty_config"
        config_dir.mkdir()

        for name in ["iterations.json", "metrics.json"]:
            shutil.copy(fixtures_dir / name, config_dir / name)

        runs = {
            "runs": [
                {
                    "id": "run-001",
                    "name": "Pending run",
                    "iteration_ids": ["v1-baseline"],
                    "metric_ids": ["exec_time"],
                    "status": "pending",
                    "created_at": "2025-02-14T15:00:00Z",
                }
            ]
        }
        (config_dir / "runs.json").write_text(json.dumps(runs, indent=2))

        reporter = BenchmarkReporter(config_dir)
        report = reporter.generate_report()

        assert "No completed runs" in report

    def test_comparison_table_structure(
        self, tmp_path: Path, fixtures_dir: Path
    ) -> None:
        config_dir = _setup_config_with_results(tmp_path, fixtures_dir)
        reporter = BenchmarkReporter(config_dir)
        report = reporter.generate_report()

        # Check table structure
        assert "| Metric |" in report
        assert "|---|" in report
        assert "Baseline approach" in report
        assert "Optimized approach" in report

    def test_percentage_difference_in_narrative(
        self, tmp_path: Path, fixtures_dir: Path
    ) -> None:
        config_dir = _setup_config_with_results(tmp_path, fixtures_dir)
        reporter = BenchmarkReporter(config_dir)
        report = reporter.generate_report()

        # Should show percentage difference
        assert "differs by" in report
        assert "%" in report
