"""Decorators for metric measurement functions."""

from __future__ import annotations

import functools
import time
from collections.abc import Callable
from typing import Any

from .base import MetricResult


def timed(func: Callable[..., MetricResult]) -> Callable[..., MetricResult]:
    """Decorator that records wall-clock time in the result metadata.

    Adds a 'wall_time_seconds' key to the MetricResult's metadata dict.
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> MetricResult:
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        result.metadata["wall_time_seconds"] = elapsed
        return result

    return wrapper


def requires_gpu(func: Callable[..., MetricResult]) -> Callable[..., MetricResult]:
    """Decorator that checks GPU availability before execution.

    Raises:
        RuntimeError: If no CUDA GPU is available.
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> MetricResult:
        try:
            import torch  # type: ignore[import-not-found]
        except ImportError as err:
            raise RuntimeError("GPU required but torch is not installed") from err
        if not torch.cuda.is_available():
            raise RuntimeError("GPU required but CUDA is not available")
        return func(*args, **kwargs)

    return wrapper
