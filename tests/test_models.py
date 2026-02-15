"""Tests for Pydantic models and JSON schema generation."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from benchmark_framework.models import (
    Iteration,
    IterationsConfig,
    MetricDefinition,
    MetricsConfig,
    ResultsConfig,
    RunDefinition,
    RunResult,
    RunsConfig,
)

SCHEMAS_DIR = Path(__file__).parent.parent / "schemas"


class TestIteration:
    def test_minimal(self) -> None:
        it = Iteration(
            id="v1",
            name="Baseline",
            approach="baseline",
            source_path="iterations/v1/",
            created_at=datetime(2025, 1, 1, tzinfo=UTC),
        )
        assert it.id == "v1"
        assert it.entry_point == "main.py"
        assert it.parameters == {}
        assert it.parent is None
        assert it.tags == []

    def test_full(self) -> None:
        it = Iteration(
            id="v2-tuned",
            name="Tuned variant",
            description="LR sweep",
            approach="transformer",
            source_path="iterations/v2/",
            entry_point="train.py",
            parameters={"lr": 0.001, "epochs": 5},
            parent="v2-base",
            created_at=datetime(2025, 2, 14, tzinfo=UTC),
            tags=["tuning", "transformer"],
        )
        assert it.parent == "v2-base"
        assert it.parameters["lr"] == 0.001
        assert "tuning" in it.tags

    def test_missing_required_field(self) -> None:
        with pytest.raises(ValidationError):
            Iteration(id="v1", name="Test")  # type: ignore[call-arg]


class TestMetricDefinition:
    def test_with_class_alias(self) -> None:
        md = MetricDefinition(
            id="exec_time",
            name="Execution Time",
            type="performance",
            higher_is_better=False,
            unit="seconds",
            **{"class": "benchmark_framework.metrics.timing.ExecutionTimeMetric"},
        )
        assert md.class_ref == "benchmark_framework.metrics.timing.ExecutionTimeMetric"
        assert md.higher_is_better is False

    def test_serialization_uses_class_key(self) -> None:
        md = MetricDefinition(
            id="acc",
            name="Accuracy",
            type="ml_quality",
            higher_is_better=True,
            unit="%",
            **{"class": "some.module.AccuracyMetric"},
        )
        data = md.model_dump(by_alias=True)
        assert "class" in data
        assert "class_ref" not in data

    def test_from_json_with_class_key(self) -> None:
        raw = {
            "id": "f1",
            "name": "F1",
            "type": "ml_quality",
            "class": "some.module.F1Metric",
            "higher_is_better": True,
        }
        md = MetricDefinition.model_validate(raw)
        assert md.class_ref == "some.module.F1Metric"


class TestRunDefinition:
    def test_defaults(self) -> None:
        rd = RunDefinition(
            id="run-001",
            name="Test run",
            iteration_ids=["v1"],
            metric_ids=["exec_time"],
            created_at=datetime(2025, 2, 14, tzinfo=UTC),
        )
        assert rd.status == "pending"
        assert rd.description == ""

    def test_full(self) -> None:
        rd = RunDefinition(
            id="run-002",
            name="Full run",
            description="All iterations, all metrics",
            iteration_ids=["v1", "v2"],
            metric_ids=["exec_time", "accuracy"],
            status="completed",
            created_at=datetime(2025, 2, 14, tzinfo=UTC),
        )
        assert rd.status == "completed"
        assert len(rd.iteration_ids) == 2


class TestRunResult:
    def test_minimal(self) -> None:
        rr = RunResult(
            run_id="run-001",
            iteration_id="v1",
            metric_id="exec_time",
            value=1.23,
            executed_at=datetime(2025, 2, 14, tzinfo=UTC),
        )
        assert rr.value == 1.23
        assert rr.unit == ""
        assert rr.environment == {}
        assert rr.metadata == {}

    def test_full(self) -> None:
        rr = RunResult(
            run_id="run-001",
            iteration_id="v2",
            metric_id="accuracy",
            value=91.7,
            unit="%",
            executed_at=datetime(2025, 2, 14, tzinfo=UTC),
            environment={"platform": "linux", "python": "3.11.7"},
            metadata={"dataset_size": 10000},
        )
        assert rr.environment["platform"] == "linux"
        assert rr.metadata["dataset_size"] == 10000


class TestConfigModels:
    def test_iterations_config(self) -> None:
        config = IterationsConfig(
            project="demo",
            iterations=[
                Iteration(
                    id="v1",
                    name="Baseline",
                    approach="baseline",
                    source_path="iterations/v1/",
                    created_at=datetime(2025, 1, 1, tzinfo=UTC),
                )
            ],
        )
        assert config.project == "demo"
        assert len(config.iterations) == 1

    def test_metrics_config(self) -> None:
        config = MetricsConfig(
            metrics=[
                MetricDefinition(
                    id="exec_time",
                    name="Execution Time",
                    type="performance",
                    higher_is_better=False,
                    unit="seconds",
                    **{
                        "class": (
                            "benchmark_framework.metrics.timing.ExecutionTimeMetric"
                        )
                    },
                )
            ]
        )
        assert len(config.metrics) == 1

    def test_runs_config(self) -> None:
        config = RunsConfig(
            runs=[
                RunDefinition(
                    id="run-001",
                    name="Test",
                    iteration_ids=["v1"],
                    metric_ids=["exec_time"],
                    created_at=datetime(2025, 2, 14, tzinfo=UTC),
                )
            ]
        )
        assert len(config.runs) == 1

    def test_results_config_empty(self) -> None:
        config = ResultsConfig()
        assert config.results == []

    def test_results_config_with_data(self) -> None:
        config = ResultsConfig(
            results=[
                RunResult(
                    run_id="run-001",
                    iteration_id="v1",
                    metric_id="exec_time",
                    value=1.5,
                    executed_at=datetime(2025, 2, 14, tzinfo=UTC),
                )
            ]
        )
        assert len(config.results) == 1


class TestJsonRoundTrip:
    def test_iteration_roundtrip(self) -> None:
        it = Iteration(
            id="v1",
            name="Baseline",
            approach="baseline",
            source_path="iterations/v1/",
            created_at=datetime(2025, 1, 1, tzinfo=UTC),
        )
        data = json.loads(it.model_dump_json())
        it2 = Iteration.model_validate(data)
        assert it == it2

    def test_metric_definition_roundtrip(self) -> None:
        md = MetricDefinition(
            id="exec_time",
            name="Execution Time",
            type="performance",
            higher_is_better=False,
            unit="seconds",
            **{"class": "benchmark_framework.metrics.timing.ExecutionTimeMetric"},
        )
        data = json.loads(md.model_dump_json(by_alias=True))
        md2 = MetricDefinition.model_validate(data)
        assert md == md2

    def test_full_config_roundtrip(self) -> None:
        config = IterationsConfig(
            project="test",
            iterations=[
                Iteration(
                    id="v1",
                    name="Test",
                    approach="test",
                    source_path="src/",
                    created_at=datetime(2025, 1, 1, tzinfo=UTC),
                    parameters={"lr": 0.01},
                    tags=["test"],
                )
            ],
        )
        json_str = config.model_dump_json()
        config2 = IterationsConfig.model_validate_json(json_str)
        assert config == config2


class TestSchemaExport:
    def test_schemas_exist(self) -> None:
        for name in [
            "iterations.schema.json",
            "metrics.schema.json",
            "runs.schema.json",
            "results.schema.json",
        ]:
            path = SCHEMAS_DIR / name
            assert path.exists(), f"Schema file missing: {name}"

    def test_schemas_are_valid_json(self) -> None:
        for path in SCHEMAS_DIR.glob("*.schema.json"):
            data = json.loads(path.read_text())
            assert "properties" in data or "$defs" in data
