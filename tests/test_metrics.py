"""Tests for BaseMetric, decorators, and timing metrics."""

from __future__ import annotations

import os
import tempfile
from typing import Any
from unittest.mock import patch

import pytest

from benchmark_framework.metrics.base import BaseMetric, MetricResult
from benchmark_framework.metrics.decorators import requires_gpu, timed
from benchmark_framework.metrics.timing import ExecutionTimeMetric


class DummyMetric(BaseMetric):
    """Concrete metric for testing the ABC."""

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
        )


class TestMetricResult:
    def test_defaults(self) -> None:
        r = MetricResult(metric_id="test", value=1.0, unit="s")
        assert r.metadata == {}

    def test_with_metadata(self) -> None:
        r = MetricResult(
            metric_id="test",
            value=1.0,
            unit="s",
            metadata={"key": "val"},
        )
        assert r.metadata["key"] == "val"


class TestBaseMetric:
    def test_cannot_instantiate_abc(self) -> None:
        with pytest.raises(TypeError):
            BaseMetric(metric_id="x", higher_is_better=True)  # type: ignore[abstract]

    def test_concrete_subclass(self) -> None:
        m = DummyMetric(metric_id="dummy", higher_is_better=True, unit="pts")
        assert m.metric_id == "dummy"
        assert m.higher_is_better is True
        result = m.measure("path", "main.py", {})
        assert result.value == 42.0

    def test_setup_teardown_are_noop(self) -> None:
        m = DummyMetric(metric_id="dummy", higher_is_better=True)
        m.setup()
        m.teardown()


class TestTimedDecorator:
    def test_adds_wall_time(self) -> None:
        m = DummyMetric(metric_id="dummy", higher_is_better=True, unit="pts")
        m.measure = timed(m.measure)  # type: ignore[method-assign]
        result = m.measure("path", "main.py", {})
        assert "wall_time_seconds" in result.metadata
        assert result.metadata["wall_time_seconds"] >= 0


class TestRequiresGpuDecorator:
    def test_raises_without_cuda(self) -> None:
        m = DummyMetric(metric_id="dummy", higher_is_better=True)

        @requires_gpu
        def gpu_measure(*args: Any, **kwargs: Any) -> MetricResult:
            return MetricResult(metric_id="dummy", value=1.0, unit="s")

        with pytest.raises(RuntimeError, match="GPU required"):
            gpu_measure()


class TestExecutionTimeMetric:
    def test_measures_simple_script(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            script = os.path.join(tmpdir, "main.py")
            with open(script, "w") as f:
                f.write("print('hello')\n")

            metric = ExecutionTimeMetric()
            result = metric.measure(tmpdir, "main.py", {})
            assert result.metric_id == "exec_time"
            assert result.value > 0
            assert result.unit == "seconds"
            assert "wall_time_seconds" in result.metadata

    def test_raises_on_missing_script(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            metric = ExecutionTimeMetric()
            with pytest.raises(FileNotFoundError):
                metric.measure(tmpdir, "nonexistent.py", {})

    def test_raises_on_failing_script(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            script = os.path.join(tmpdir, "main.py")
            with open(script, "w") as f:
                f.write("raise SystemExit(1)\n")

            metric = ExecutionTimeMetric()
            with pytest.raises(RuntimeError, match="Iteration failed"):
                metric.measure(tmpdir, "main.py", {})

    def test_custom_metric_id(self) -> None:
        metric = ExecutionTimeMetric(metric_id="custom_time")
        assert metric.metric_id == "custom_time"
        assert metric.higher_is_better is False
