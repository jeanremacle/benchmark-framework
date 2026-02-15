"""Registry for loading and validating benchmark JSON configurations."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import TYPE_CHECKING

from .models import (
    IterationsConfig,
    MetricsConfig,
    ResultsConfig,
    RunsConfig,
)

if TYPE_CHECKING:
    from .metrics.base import BaseMetric


class RegistryError(Exception):
    """Raised when registry loading or validation fails."""


class Registry:
    """Loads and validates benchmark JSON configuration files.

    Provides methods to load each config file type and resolve metric
    class references to their Python implementations.
    """

    @staticmethod
    def load_iterations(path: str | Path) -> IterationsConfig:
        """Load and validate iterations.json.

        Args:
            path: Path to the iterations.json file.

        Returns:
            Validated IterationsConfig.

        Raises:
            RegistryError: If the file cannot be read or validated.
        """
        return Registry._load(path, IterationsConfig)

    @staticmethod
    def load_metrics(path: str | Path) -> MetricsConfig:
        """Load and validate metrics.json.

        Args:
            path: Path to the metrics.json file.

        Returns:
            Validated MetricsConfig.

        Raises:
            RegistryError: If the file cannot be read or validated.
        """
        return Registry._load(path, MetricsConfig)

    @staticmethod
    def load_runs(path: str | Path) -> RunsConfig:
        """Load and validate runs.json.

        Args:
            path: Path to the runs.json file.

        Returns:
            Validated RunsConfig.

        Raises:
            RegistryError: If the file cannot be read or validated.
        """
        return Registry._load(path, RunsConfig)

    @staticmethod
    def load_results(path: str | Path) -> ResultsConfig:
        """Load and validate results.json.

        Args:
            path: Path to the results.json file.

        Returns:
            Validated ResultsConfig. Returns empty config if file
            does not exist.

        Raises:
            RegistryError: If the file exists but cannot be validated.
        """
        filepath = Path(path)
        if not filepath.exists():
            return ResultsConfig(results=[])
        return Registry._load(filepath, ResultsConfig)

    @staticmethod
    def resolve_metric_class(class_ref: str) -> type[BaseMetric]:
        """Dynamically import and return a metric class from its reference.

        Args:
            class_ref: Fully-qualified class reference
                (e.g. 'benchmark_framework.metrics.timing.ExecutionTimeMetric').

        Returns:
            The metric class (not an instance).

        Raises:
            RegistryError: If the module or class cannot be imported.
        """
        try:
            module_path, class_name = class_ref.rsplit(".", 1)
            module = importlib.import_module(module_path)
            cls = getattr(module, class_name)
        except (ValueError, ModuleNotFoundError, AttributeError) as err:
            raise RegistryError(
                f"Cannot resolve metric class '{class_ref}': {err}"
            ) from err

        from .metrics.base import BaseMetric

        if not (isinstance(cls, type) and issubclass(cls, BaseMetric)):
            raise RegistryError(
                f"'{class_ref}' is not a subclass of BaseMetric"
            )

        return cls  # type: ignore[return-value]

    @staticmethod
    def _load[T](path: str | Path, model: type[T]) -> T:
        """Load a JSON file and validate it against a Pydantic model.

        Args:
            path: Path to the JSON file.
            model: Pydantic model class to validate against.

        Returns:
            Validated model instance.

        Raises:
            RegistryError: If the file cannot be read or validated.
        """
        filepath = Path(path)
        try:
            raw = filepath.read_text(encoding="utf-8")
        except OSError as err:
            raise RegistryError(f"Cannot read '{filepath}': {err}") from err

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as err:
            raise RegistryError(
                f"Invalid JSON in '{filepath}': {err}"
            ) from err

        try:
            return model.model_validate(data)  # type: ignore[union-attr]
        except Exception as err:
            raise RegistryError(
                f"Validation failed for '{filepath}': {err}"
            ) from err
