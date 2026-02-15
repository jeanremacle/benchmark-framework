"""Public stable API for the benchmark framework.

This module is the contract for external consumers. Internal modules
may be refactored freely as long as this interface remains stable.

Usage:
    from benchmark_framework.api import execute_run, generate_report

    results = execute_run(run_id="run-001", config_dir="path/to/config/")
    report = generate_report(config_dir="path/to/config/", output_path="report.md")
"""

from __future__ import annotations

from pathlib import Path

from .models import (
    Iteration,
    IterationsConfig,
    MetricDefinition,
    MetricsConfig,
    ResultsConfig,
    RunDefinition,
    RunResult,
    RunsConfig,
)
from .registry import Registry
from .reporter import BenchmarkReporter
from .runner import BenchmarkRunner

# Re-export key types for consumers
__all__ = [
    "Iteration",
    "IterationsConfig",
    "MetricDefinition",
    "MetricsConfig",
    "ResultsConfig",
    "RunDefinition",
    "RunResult",
    "RunsConfig",
    "execute_run",
    "generate_report",
    "load_iterations",
    "load_metrics",
    "load_results",
    "load_runs",
]


def load_iterations(path: str | Path) -> IterationsConfig:
    """Load and validate an iterations.json file.

    Args:
        path: Path to the iterations.json file.

    Returns:
        Validated IterationsConfig.
    """
    return Registry.load_iterations(path)


def load_metrics(path: str | Path) -> MetricsConfig:
    """Load and validate a metrics.json file.

    Args:
        path: Path to the metrics.json file.

    Returns:
        Validated MetricsConfig.
    """
    return Registry.load_metrics(path)


def load_runs(path: str | Path) -> RunsConfig:
    """Load and validate a runs.json file.

    Args:
        path: Path to the runs.json file.

    Returns:
        Validated RunsConfig.
    """
    return Registry.load_runs(path)


def load_results(path: str | Path) -> ResultsConfig:
    """Load and validate a results.json file.

    Args:
        path: Path to the results.json file.

    Returns:
        Validated ResultsConfig (empty if file does not exist).
    """
    return Registry.load_results(path)


def execute_run(
    run_id: str, config_dir: str | Path
) -> list[RunResult]:
    """Execute a benchmark run.

    Convenience wrapper that creates a BenchmarkRunner, executes the
    specified run, and returns the results.

    Args:
        run_id: ID of the run to execute (must exist in runs.json).
        config_dir: Path to the directory containing JSON config files.

    Returns:
        List of RunResult objects from this execution.
    """
    runner = BenchmarkRunner(config_dir)
    return runner.execute_run(run_id)


def generate_report(
    config_dir: str | Path,
    output_path: str | Path | None = None,
) -> str:
    """Generate a Markdown comparison report.

    Args:
        config_dir: Path to the directory containing JSON config files.
        output_path: Optional path to write the report file.

    Returns:
        The full Markdown report as a string.
    """
    reporter = BenchmarkReporter(config_dir)
    return reporter.generate_report(output_path=output_path)
