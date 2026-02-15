"""Benchmark runner for sequential execution of iterations x metrics."""

from __future__ import annotations

import json
import logging
import platform
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .models import (
    Iteration,
    MetricDefinition,
    RunDefinition,
    RunResult,
)
from .registry import Registry

logger = logging.getLogger(__name__)


class RunnerError(Exception):
    """Raised when a benchmark run fails."""


class BenchmarkRunner:
    """Executes benchmark runs sequentially.

    For each run, iterates over all iteration x metric combinations,
    collects results, and appends them to results.json.

    Args:
        config_dir: Path to the directory containing JSON config files.
    """

    def __init__(self, config_dir: str | Path) -> None:
        self.config_dir = Path(config_dir)
        self.iterations_config = Registry.load_iterations(
            self.config_dir / "iterations.json"
        )
        self.metrics_config = Registry.load_metrics(self.config_dir / "metrics.json")
        self.runs_config = Registry.load_runs(self.config_dir / "runs.json")
        self.results_path = self.config_dir / "results.json"

    def execute_run(self, run_id: str) -> list[RunResult]:
        """Execute a single benchmark run.

        Args:
            run_id: ID of the run to execute (must exist in runs.json).

        Returns:
            List of RunResult objects from this execution.

        Raises:
            RunnerError: If run_id is not found or execution fails.
        """
        run_def = self._find_run(run_id)
        if run_def.status == "completed":
            logger.warning("Run '%s' is already completed, re-running", run_id)

        iterations = self._resolve_iterations(run_def.iteration_ids)
        metrics = self._resolve_metrics(run_def.metric_ids)

        results: list[RunResult] = []
        run_def.status = "running"

        try:
            for iteration in iterations:
                for metric_def in metrics:
                    result = self._measure(run_def, iteration, metric_def)
                    results.append(result)
            run_def.status = "completed"
        except Exception as err:
            run_def.status = "failed"
            logger.error("Run '%s' failed: %s", run_id, err)
            raise RunnerError(f"Run '{run_id}' failed: {err}") from err
        finally:
            self._save_results(results)
            self._save_run_status(run_def)

        return results

    def _find_run(self, run_id: str) -> RunDefinition:
        """Find a run definition by ID."""
        for run in self.runs_config.runs:
            if run.id == run_id:
                return run
        raise RunnerError(f"Run '{run_id}' not found in runs.json")

    def _resolve_iterations(self, ids: list[str]) -> list[Iteration]:
        """Resolve iteration IDs to Iteration objects."""
        iteration_map = {it.id: it for it in self.iterations_config.iterations}
        result = []
        for iter_id in ids:
            if iter_id not in iteration_map:
                raise RunnerError(f"Iteration '{iter_id}' not found in iterations.json")
            result.append(iteration_map[iter_id])
        return result

    def _resolve_metrics(self, ids: list[str]) -> list[MetricDefinition]:
        """Resolve metric IDs to MetricDefinition objects."""
        metric_map = {m.id: m for m in self.metrics_config.metrics}
        result = []
        for metric_id in ids:
            if metric_id not in metric_map:
                raise RunnerError(f"Metric '{metric_id}' not found in metrics.json")
            result.append(metric_map[metric_id])
        return result

    def _measure(
        self,
        run_def: RunDefinition,
        iteration: Iteration,
        metric_def: MetricDefinition,
    ) -> RunResult:
        """Execute a single metric measurement on an iteration."""
        logger.info("Measuring '%s' on '%s'", metric_def.id, iteration.id)

        metric_cls = Registry.resolve_metric_class(metric_def.class_ref)
        metric_instance = metric_cls(
            metric_id=metric_def.id,
            higher_is_better=metric_def.higher_is_better,
            unit=metric_def.unit,
        )

        iteration_path = str(self.config_dir / iteration.source_path)

        metric_instance.setup()
        try:
            metric_result = metric_instance.measure(
                iteration_path=iteration_path,
                entry_point=iteration.entry_point,
                parameters=iteration.parameters,
            )
        finally:
            metric_instance.teardown()

        return RunResult(
            run_id=run_def.id,
            iteration_id=iteration.id,
            metric_id=metric_def.id,
            value=metric_result.value,
            unit=metric_result.unit,
            executed_at=datetime.now(UTC),
            environment=self._get_environment(),
            metadata=metric_result.metadata,
        )

    def _get_environment(self) -> dict[str, Any]:
        """Capture current execution environment."""
        return {
            "platform": platform.platform(),
            "python": sys.version.split()[0],
            "machine": platform.machine(),
        }

    def _save_results(self, new_results: list[RunResult]) -> None:
        """Append results to results.json (append-only)."""
        existing = Registry.load_results(self.results_path)
        existing.results.extend(new_results)

        data = existing.model_dump(mode="json")
        self.results_path.write_text(
            json.dumps(data, indent=2, default=str) + "\n",
            encoding="utf-8",
        )

    def _save_run_status(self, run_def: RunDefinition) -> None:
        """Update the run status in runs.json."""
        for run in self.runs_config.runs:
            if run.id == run_def.id:
                run.status = run_def.status
                break

        data = self.runs_config.model_dump(mode="json")
        runs_path = self.config_dir / "runs.json"
        runs_path.write_text(
            json.dumps(data, indent=2, default=str) + "\n",
            encoding="utf-8",
        )
