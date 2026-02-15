.PHONY: setup test lint clean benchmark-demo

setup:
	uv sync --all-extras

test:
	uv run pytest -v --cov=benchmark_framework

lint:
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy src/

format:
	uv run ruff format .
	uv run ruff check --fix .

clean:
	rm -rf .venv __pycache__ .pytest_cache .mypy_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} +

benchmark-demo:
	uv run python -m benchmark_framework.runner examples/demo/
