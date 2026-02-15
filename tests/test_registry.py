"""Tests for the Registry configuration loader."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from benchmark_framework.metrics.timing import ExecutionTimeMetric
from benchmark_framework.registry import Registry, RegistryError


class TestLoadIterations:
    def test_loads_valid_file(self, iterations_path: Path) -> None:
        config = Registry.load_iterations(iterations_path)
        assert config.project == "test-project"
        assert len(config.iterations) == 2
        assert config.iterations[0].id == "v1-baseline"
        assert config.iterations[1].parent == "v1-baseline"

    def test_raises_on_missing_file(self) -> None:
        with pytest.raises(RegistryError, match="Cannot read"):
            Registry.load_iterations("/nonexistent/iterations.json")

    def test_raises_on_invalid_json(self, tmp_path: Path) -> None:
        bad_file = tmp_path / "iterations.json"
        bad_file.write_text("not json")
        with pytest.raises(RegistryError, match="Invalid JSON"):
            Registry.load_iterations(bad_file)

    def test_raises_on_invalid_schema(self, tmp_path: Path) -> None:
        bad_file = tmp_path / "iterations.json"
        bad_file.write_text(json.dumps({"iterations": [{"bad": "data"}]}))
        with pytest.raises(RegistryError, match="Validation failed"):
            Registry.load_iterations(bad_file)


class TestLoadMetrics:
    def test_loads_valid_file(self, metrics_path: Path) -> None:
        config = Registry.load_metrics(metrics_path)
        assert len(config.metrics) == 1
        assert config.metrics[0].id == "exec_time"
        assert config.metrics[0].class_ref == (
            "benchmark_framework.metrics.timing.ExecutionTimeMetric"
        )
        assert config.metrics[0].higher_is_better is False


class TestLoadRuns:
    def test_loads_valid_file(self, runs_path: Path) -> None:
        config = Registry.load_runs(runs_path)
        assert len(config.runs) == 1
        assert config.runs[0].id == "run-001"
        assert config.runs[0].status == "pending"


class TestLoadResults:
    def test_returns_empty_for_missing_file(self) -> None:
        config = Registry.load_results("/nonexistent/results.json")
        assert config.results == []

    def test_loads_existing_file(self, tmp_path: Path) -> None:
        results_file = tmp_path / "results.json"
        results_file.write_text(
            json.dumps(
                {
                    "results": [
                        {
                            "run_id": "run-001",
                            "iteration_id": "v1",
                            "metric_id": "exec_time",
                            "value": 1.5,
                            "executed_at": "2025-02-14T16:00:00Z",
                        }
                    ]
                }
            )
        )
        config = Registry.load_results(results_file)
        assert len(config.results) == 1
        assert config.results[0].value == 1.5


class TestResolveMetricClass:
    def test_resolves_execution_time_metric(self) -> None:
        cls = Registry.resolve_metric_class(
            "benchmark_framework.metrics.timing.ExecutionTimeMetric"
        )
        assert cls is ExecutionTimeMetric

    def test_raises_on_bad_module(self) -> None:
        with pytest.raises(RegistryError, match="Cannot resolve"):
            Registry.resolve_metric_class("nonexistent.module.SomeMetric")

    def test_raises_on_bad_class(self) -> None:
        with pytest.raises(RegistryError, match="Cannot resolve"):
            Registry.resolve_metric_class(
                "benchmark_framework.metrics.timing.NonexistentClass"
            )

    def test_raises_on_non_metric_class(self) -> None:
        with pytest.raises(RegistryError, match="not a subclass"):
            Registry.resolve_metric_class(
                "benchmark_framework.models.Iteration"
            )

    def test_raises_on_invalid_reference(self) -> None:
        with pytest.raises(RegistryError, match="Cannot resolve"):
            Registry.resolve_metric_class("nodotshere")
