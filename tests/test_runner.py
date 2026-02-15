"""Tests for BenchmarkRunner."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from benchmark_framework.metrics.base import BaseMetric, MetricResult
from benchmark_framework.runner import BenchmarkRunner, RunnerError


class MockMetric(BaseMetric):
    """Mock metric that returns a fixed value."""

    def measure(
        self,
        iteration_path: str,
        entry_point: str,
        parameters: dict[str, Any],
    ) -> MetricResult:
        return MetricResult(
            metric_id=self.metric_id,
            value=42.0,
            unit=self.unit,
            metadata={"mock": True},
        )


class FailingMetric(BaseMetric):
    """Mock metric that always raises."""

    def measure(
        self,
        iteration_path: str,
        entry_point: str,
        parameters: dict[str, Any],
    ) -> MetricResult:
        raise RuntimeError("Measurement failed")


def _setup_config_dir(tmp_path: Path, fixtures_dir: Path) -> Path:
    """Copy fixtures to tmp_path and add iteration directories."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    for name in ["iterations.json", "metrics.json", "runs.json"]:
        shutil.copy(fixtures_dir / name, config_dir / name)

    # Create iteration source directories
    iter_dir = config_dir / "iterations" / "v1_baseline"
    iter_dir.mkdir(parents=True)
    (iter_dir / "main.py").write_text("print('baseline')\n")

    iter_dir2 = config_dir / "iterations" / "v2_optimized"
    iter_dir2.mkdir(parents=True)
    (iter_dir2 / "main.py").write_text("print('optimized')\n")

    return config_dir


class TestBenchmarkRunner:
    def test_execute_run_with_mock(self, tmp_path: Path, fixtures_dir: Path) -> None:
        config_dir = _setup_config_dir(tmp_path, fixtures_dir)

        with patch(
            "benchmark_framework.runner.Registry.resolve_metric_class",
            return_value=MockMetric,
        ):
            runner = BenchmarkRunner(config_dir)
            results = runner.execute_run("run-001")

        assert len(results) == 1
        assert results[0].run_id == "run-001"
        assert results[0].iteration_id == "v1-baseline"
        assert results[0].metric_id == "exec_time"
        assert results[0].value == 42.0

        # Verify results.json was created
        results_path = config_dir / "results.json"
        assert results_path.exists()
        data = json.loads(results_path.read_text())
        assert len(data["results"]) == 1

    def test_run_updates_status_to_completed(
        self, tmp_path: Path, fixtures_dir: Path
    ) -> None:
        config_dir = _setup_config_dir(tmp_path, fixtures_dir)

        with patch(
            "benchmark_framework.runner.Registry.resolve_metric_class",
            return_value=MockMetric,
        ):
            runner = BenchmarkRunner(config_dir)
            runner.execute_run("run-001")

        runs_data = json.loads((config_dir / "runs.json").read_text())
        assert runs_data["runs"][0]["status"] == "completed"

    def test_run_updates_status_to_failed(
        self, tmp_path: Path, fixtures_dir: Path
    ) -> None:
        config_dir = _setup_config_dir(tmp_path, fixtures_dir)

        with (
            patch(
                "benchmark_framework.runner.Registry.resolve_metric_class",
                return_value=FailingMetric,
            ),
            pytest.raises(RunnerError, match="failed"),
        ):
            runner = BenchmarkRunner(config_dir)
            runner.execute_run("run-001")

        runs_data = json.loads((config_dir / "runs.json").read_text())
        assert runs_data["runs"][0]["status"] == "failed"

    def test_raises_on_unknown_run(self, tmp_path: Path, fixtures_dir: Path) -> None:
        config_dir = _setup_config_dir(tmp_path, fixtures_dir)
        runner = BenchmarkRunner(config_dir)

        with pytest.raises(RunnerError, match="not found"):
            runner.execute_run("nonexistent-run")

    def test_append_only_results(self, tmp_path: Path, fixtures_dir: Path) -> None:
        config_dir = _setup_config_dir(tmp_path, fixtures_dir)

        with patch(
            "benchmark_framework.runner.Registry.resolve_metric_class",
            return_value=MockMetric,
        ):
            runner = BenchmarkRunner(config_dir)

            # Reset status before each run
            runs_data = json.loads((config_dir / "runs.json").read_text())
            runs_data["runs"][0]["status"] = "pending"
            (config_dir / "runs.json").write_text(json.dumps(runs_data, indent=2))
            runner = BenchmarkRunner(config_dir)
            runner.execute_run("run-001")

            runs_data = json.loads((config_dir / "runs.json").read_text())
            runs_data["runs"][0]["status"] = "pending"
            (config_dir / "runs.json").write_text(json.dumps(runs_data, indent=2))
            runner = BenchmarkRunner(config_dir)
            runner.execute_run("run-001")

        data = json.loads((config_dir / "results.json").read_text())
        assert len(data["results"]) == 2

    def test_environment_captured(self, tmp_path: Path, fixtures_dir: Path) -> None:
        config_dir = _setup_config_dir(tmp_path, fixtures_dir)

        with patch(
            "benchmark_framework.runner.Registry.resolve_metric_class",
            return_value=MockMetric,
        ):
            runner = BenchmarkRunner(config_dir)
            results = runner.execute_run("run-001")

        env = results[0].environment
        assert "platform" in env
        assert "python" in env
