"""Base metric class and result dataclass for the benchmark framework."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MetricResult:
    """Result of a single metric measurement."""

    metric_id: str
    value: float
    unit: str
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseMetric(ABC):
    """Abstract base class for all benchmark metrics.

    Subclasses must implement the `measure` method. Optional `setup` and
    `teardown` hooks are available for resource management.

    Attributes:
        metric_id: Unique identifier matching the metrics.json definition.
        higher_is_better: Whether higher values indicate better performance.
        unit: Unit of measurement for the metric value.
    """

    def __init__(
        self,
        metric_id: str,
        higher_is_better: bool,
        unit: str = "",
    ) -> None:
        self.metric_id = metric_id
        self.higher_is_better = higher_is_better
        self.unit = unit

    @abstractmethod
    def measure(
        self,
        iteration_path: str,
        entry_point: str,
        parameters: dict[str, Any],
    ) -> MetricResult:
        """Execute the measurement on a given iteration.

        Args:
            iteration_path: Path to the iteration source code directory.
            entry_point: Entry point file to execute within iteration_path.
            parameters: Hyperparameters for the iteration.

        Returns:
            MetricResult with the measured value.
        """
        ...

    def setup(self) -> None:
        """Optional hook called before measurement."""

    def teardown(self) -> None:
        """Optional hook called after measurement."""
