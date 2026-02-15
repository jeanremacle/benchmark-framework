"""Timing-based metric implementations."""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from .base import BaseMetric, MetricResult
from .decorators import timed


class ExecutionTimeMetric(BaseMetric):
    """Measures wall-clock execution time of an iteration's entry point.

    Runs the entry point as a subprocess and measures elapsed time.
    """

    def __init__(
        self,
        metric_id: str = "exec_time",
        higher_is_better: bool = False,
        unit: str = "seconds",
    ) -> None:
        super().__init__(
            metric_id=metric_id,
            higher_is_better=higher_is_better,
            unit=unit,
        )

    @timed
    def measure(
        self,
        iteration_path: str,
        entry_point: str,
        parameters: dict[str, Any],
    ) -> MetricResult:
        """Measure execution time by running the entry point as a subprocess.

        Args:
            iteration_path: Path to the iteration source directory.
            entry_point: Python file to execute.
            parameters: Passed as JSON via --params argument (unused by default).

        Returns:
            MetricResult with execution time in seconds.
        """
        script = Path(iteration_path) / entry_point
        if not script.exists():
            raise FileNotFoundError(f"Entry point not found: {script}")

        start = time.perf_counter()
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
            cwd=str(Path(iteration_path)),
            check=False,
        )
        elapsed = time.perf_counter() - start

        if result.returncode != 0:
            raise RuntimeError(
                f"Iteration failed (exit code {result.returncode}): "
                f"{result.stderr.strip()}"
            )

        return MetricResult(
            metric_id=self.metric_id,
            value=elapsed,
            unit=self.unit,
            metadata={
                "stdout_lines": len(result.stdout.splitlines()),
                "returncode": result.returncode,
            },
        )
