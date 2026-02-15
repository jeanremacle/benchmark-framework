"""Shared test fixtures for the benchmark framework."""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    """Path to the test fixtures directory."""
    return FIXTURES_DIR


@pytest.fixture
def iterations_path(fixtures_dir: Path) -> Path:
    """Path to the test iterations.json."""
    return fixtures_dir / "iterations.json"


@pytest.fixture
def metrics_path(fixtures_dir: Path) -> Path:
    """Path to the test metrics.json."""
    return fixtures_dir / "metrics.json"


@pytest.fixture
def runs_path(fixtures_dir: Path) -> Path:
    """Path to the test runs.json."""
    return fixtures_dir / "runs.json"
