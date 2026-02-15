"""Pydantic models for benchmark framework JSON schemas.

All data models are defined here as the single source of truth.
JSON schemas are derived from these models via model_json_schema().
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Iteration(BaseModel):
    """A single solution variant to benchmark."""

    id: str = Field(description="Unique identifier for this iteration")
    name: str = Field(description="Human-readable name")
    description: str = Field(default="", description="Detailed description")
    approach: str = Field(description="Approach family (e.g. 'baseline', 'transformer')")
    source_path: str = Field(description="Path to iteration source code directory")
    entry_point: str = Field(
        default="main.py", description="Entry point file within source_path"
    )
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="Hyperparameters for this iteration"
    )
    parent: str | None = Field(
        default=None, description="ID of parent iteration (for lineage tracking)"
    )
    created_at: datetime = Field(description="When this iteration was created")
    tags: list[str] = Field(
        default_factory=list, description="Tags for categorization"
    )


class MetricDefinition(BaseModel):
    """Definition of a measurement metric and its Python implementation."""

    id: str = Field(description="Unique identifier for this metric")
    name: str = Field(description="Human-readable name")
    description: str = Field(default="", description="Detailed description")
    type: str = Field(description="Metric category (e.g. 'performance', 'ml_quality')")
    class_ref: str = Field(
        alias="class",
        description="Fully-qualified Python class reference",
    )
    higher_is_better: bool = Field(
        description="Whether higher values indicate better performance"
    )
    unit: str = Field(default="", description="Unit of measurement")

    model_config = {"populate_by_name": True}


class RunDefinition(BaseModel):
    """Definition of a benchmark run: which iterations x which metrics."""

    id: str = Field(description="Unique identifier for this run")
    name: str = Field(description="Human-readable name")
    description: str = Field(default="", description="Detailed description")
    iteration_ids: list[str] = Field(
        description="IDs of iterations to include in this run"
    )
    metric_ids: list[str] = Field(
        description="IDs of metrics to measure in this run"
    )
    status: str = Field(
        default="pending",
        description="Run status: pending, running, completed, failed",
    )
    created_at: datetime = Field(description="When this run was created")


class RunResult(BaseModel):
    """Result of a single metric measurement on a single iteration."""

    run_id: str = Field(description="ID of the run that produced this result")
    iteration_id: str = Field(description="ID of the measured iteration")
    metric_id: str = Field(description="ID of the metric used")
    value: float = Field(description="Measured value")
    unit: str = Field(default="", description="Unit of measurement")
    executed_at: datetime = Field(description="When this measurement was taken")
    environment: dict[str, Any] = Field(
        default_factory=dict,
        description="Execution environment details (platform, python version, GPU)",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about this measurement",
    )


class IterationsConfig(BaseModel):
    """Root model for iterations.json."""

    project: str = Field(default="", description="Project name")
    iterations: list[Iteration] = Field(description="List of iterations")


class MetricsConfig(BaseModel):
    """Root model for metrics.json."""

    metrics: list[MetricDefinition] = Field(description="List of metric definitions")


class RunsConfig(BaseModel):
    """Root model for runs.json."""

    runs: list[RunDefinition] = Field(description="List of run definitions")


class ResultsConfig(BaseModel):
    """Root model for results.json."""

    results: list[RunResult] = Field(
        default_factory=list, description="List of run results"
    )
