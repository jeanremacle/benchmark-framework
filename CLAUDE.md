# CLAUDE.md — Benchmark Framework

## Project Identity

- **Repo**: `jeanremacle/benchmark-framework`
- **Purpose**: Generic benchmark framework for comparing iterative solutions (algorithmic approaches and/or hyperparameter variants)
- **Language**: Python 3.11+ — all code, comments, docstrings, and commit messages in English
- **Architecture doc**: See `docs/architecture-optim-jupyter.md` for full context

## Quick Reference

```bash
# Setup
make setup          # Create venv, install deps
make test           # Run all tests
make lint           # Ruff + mypy
make benchmark-demo # Run the demo benchmark

# Development
uv sync             # Sync dependencies
uv run pytest       # Run tests via uv
uv run ruff check . # Lint
uv run mypy src/    # Type check
```

## Project Structure

```text
benchmark-framework/
├── CLAUDE.md                    # This file
├── pyproject.toml               # Project config (uv-managed)
├── Makefile                     # Standard targets
├── README.md                    # Public documentation
├── docs/
│   └── architecture-optim-jupyter.md
├── src/
│   └── benchmark_framework/
│       ├── __init__.py
│       ├── api.py               # Public stable interface
│       ├── models.py            # Pydantic models for JSON schemas
│       ├── registry.py          # Load and validate JSON configs
│       ├── runner.py            # Execute runs sequentially
│       ├── reporter.py          # Generate Markdown comparison reports
│       └── metrics/
│           ├── __init__.py
│           ├── base.py          # BaseMetric ABC + MetricResult
│           ├── decorators.py    # @timed, @requires_gpu, etc.
│           ├── timing.py        # ExecutionTimeMetric, GpuMemoryMetric
│           └── ml_quality.py    # AccuracyMetric, F1MacroMetric, etc.
├── schemas/
│   ├── iterations.schema.json
│   ├── metrics.schema.json
│   ├── runs.schema.json
│   └── results.schema.json
├── tests/
│   ├── conftest.py
│   ├── test_models.py
│   ├── test_registry.py
│   ├── test_runner.py
│   ├── test_reporter.py
│   └── fixtures/               # Sample JSON files for tests
│       ├── iterations.json
│       ├── metrics.json
│       ├── runs.json
│       └── sample_iteration/
│           └── main.py
├── examples/
│   └── demo/                   # Standalone demo benchmark
│       ├── iterations.json
│       ├── metrics.json
│       ├── runs.json
│       └── iterations/
│           ├── v1_baseline/
│           │   └── main.py
│           └── v2_optimized/
│               └── main.py
└── .github/
    └── workflows/
        └── test.yml            # CI: lint + test on push/PR
```

## Coding Standards

### Style

- **Formatter/linter**: `ruff` (format + check)
- **Type checker**: `mypy` with strict mode
- **Docstrings**: Google style
- **Line length**: 88 characters (ruff default)
- **Imports**: sorted by ruff (isort-compatible)

### Architecture Rules

1. **Pydantic for all data models** — JSON schemas are derived from Pydantic models (single source of truth)
2. **ABC for metrics** — All metric classes inherit `BaseMetric`
3. **Dynamic loading** — Runner instantiates metric classes from fully-qualified class references in `metrics.json`
4. **Append-only results** — `results.json` is never truncated, only appended
5. **No side effects in models** — Models are pure data; logic lives in runner/registry/reporter
6. **Stable public API** — `api.py` is the contract; internal modules can refactor freely

### Dependency Management

- **Tool**: `uv` (not pip directly)
- **Lock file**: `uv.lock` committed to repo
- **Core deps**: `pydantic>=2.0`, `jsonschema`, `rich` (for CLI output)
- **Test deps**: `pytest`, `pytest-cov`
- **Dev deps**: `ruff`, `mypy`
- **No heavy ML deps in this repo** — metric classes that need torch/sklearn are optional extras

### Git Conventions

- **Commit messages**: Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`)
- **Branch strategy**: `main` is always releasable; feature branches for WIP
- **Tags**: Semantic versioning `v0.1.0`, `v0.2.0`, etc.

## Task Sequence (Phase 1)

Execute in order. Each task should result in a commit.

### Task 1.1 — Project Scaffolding

- Initialize `pyproject.toml` with uv
- Create directory structure (as above)
- Write `Makefile` with targets: `setup`, `test`, `lint`, `clean`
- Write minimal `README.md`
- Commit: `chore: initialize project structure`

### Task 1.2 — Pydantic Models + JSON Schemas

- Define models in `src/benchmark_framework/models.py`:
  - `Iteration` (id, name, description, approach, source_path, entry_point, parameters, parent, created_at, tags)
  - `MetricDefinition` (id, name, description, type, class_ref, higher_is_better, unit)
  - `RunDefinition` (id, name, description, iteration_ids, metric_ids, status, created_at)
  - `RunResult` (run_id, iteration_id, metric_id, value, unit, executed_at, environment, metadata)
  - `IterationsConfig`, `MetricsConfig`, `RunsConfig`, `ResultsConfig` (root models wrapping lists)
- Export JSON schemas to `schemas/` using `model_json_schema()`
- Write tests in `tests/test_models.py`
- Commit: `feat: add Pydantic models and JSON schemas`

### Task 1.3 — BaseMetric + Decorators

- Implement `BaseMetric` ABC in `src/benchmark_framework/metrics/base.py`
- Implement decorators in `src/benchmark_framework/metrics/decorators.py` (`@timed`, `@requires_gpu`)
- Implement `ExecutionTimeMetric` in `timing.py`
- Write tests
- Commit: `feat: add BaseMetric ABC and timing metrics`

### Task 1.4 — Registry

- Implement `Registry` class in `registry.py`:
  - `load_iterations(path) -> IterationsConfig`
  - `load_metrics(path) -> MetricsConfig`
  - `load_runs(path) -> RunsConfig`
  - `load_results(path) -> ResultsConfig`
  - `resolve_metric_class(class_ref: str) -> type[BaseMetric]` (dynamic import)
- Validate JSON against Pydantic models on load
- Write tests with fixture JSON files
- Commit: `feat: add Registry for JSON config loading and validation`

### Task 1.5 — Runner

- Implement `BenchmarkRunner` in `runner.py`:
  - Takes a `RunDefinition` + registry
  - Iterates: for each iteration × each metric, call `metric.measure()`
  - Collects `RunResult` objects
  - Appends to `results.json`
  - Updates run status to `"completed"` or `"failed"`
- Sequential execution (no parallelism in MVP)
- Write tests with mock metrics
- Commit: `feat: add BenchmarkRunner for sequential run execution`

### Task 1.6 — Reporter

- Implement `BenchmarkReporter` in `reporter.py`:
  - Reads `results.json`
  - Groups by run, then by metric
  - Generates Markdown comparison table
  - Highlights best iteration per metric (using `higher_is_better`)
  - Produces narrative sections explaining trade-offs
- Output: `comparison_report.md`
- Write tests
- Commit: `feat: add BenchmarkReporter for Markdown report generation`

### Task 1.7 — Public API

- Implement `api.py` as the stable public interface:
  - `load_iterations(path)`, `load_metrics(path)`, `load_runs(path)`
  - `execute_run(run_id, config_dir)` — convenience wrapper
  - `generate_report(config_dir, output_path)`
- Re-export key types from `models.py`
- Commit: `feat: add stable public API`

### Task 1.8 — Demo + CI

- Create `examples/demo/` with a toy benchmark (two simple Python scripts, trivial metrics)
- Write `.github/workflows/test.yml` (Python 3.11+, uv, lint, test)
- Verify everything works end-to-end: `make benchmark-demo`
- Tag `v0.1.0`
- Commit: `feat: add demo benchmark and CI workflow`

## JSON Schema Examples

### iterations.json

```json
{
  "project": "demo",
  "iterations": [
    {
      "id": "v1-baseline",
      "name": "Baseline approach",
      "description": "Simple implementation for reference",
      "approach": "baseline",
      "source_path": "iterations/v1_baseline/",
      "entry_point": "main.py",
      "parameters": {},
      "parent": null,
      "created_at": "2025-02-14T10:00:00Z",
      "tags": ["baseline"]
    }
  ]
}
```

### metrics.json

```json
{
  "metrics": [
    {
      "id": "exec_time",
      "name": "Execution Time",
      "description": "Wall-clock execution time",
      "type": "performance",
      "class": "benchmark_framework.metrics.timing.ExecutionTimeMetric",
      "higher_is_better": false,
      "unit": "seconds"
    }
  ]
}
```

### runs.json

```json
{
  "runs": [
    {
      "id": "run-001",
      "name": "Baseline benchmark",
      "description": "Measure baseline performance",
      "iteration_ids": ["v1-baseline"],
      "metric_ids": ["exec_time"],
      "status": "pending",
      "created_at": "2025-02-14T15:00:00Z"
    }
  ]
}
```

## Key Design Decisions

1. **Why Pydantic over raw JSON schema?** — Single source of truth. Models are used at runtime for validation AND exported to `.schema.json` for external tooling.
2. **Why dynamic class loading?** — Allows users (or an AI agent) to add new metric classes without modifying the runner. Just add a Python file and reference it in `metrics.json`.
3. **Why append-only results?** — Full history enables trend analysis and prevents accidental data loss. Filtering is done at report time.
4. **Why `uv` over pip/poetry?** — Jean's preferred toolchain. Fast, reliable, handles lockfiles well.
5. **Why no ML deps in core?** — This repo is a generic framework. ML-specific metrics (accuracy, F1) import sklearn/torch only when instantiated, as optional extras.

## Session Communication Protocol

### PM Communication Protocol

#### Inbound — directives from PM layer (read-only)

At **session start** and before beginning any new step, read `directives.md` in the project root.
This file contains current priorities, decisions, and constraints set by the project management layer.

**Rules:**

- Never modify `directives.md` — it is owned by the PM layer
- If directives conflict with `PLAN.md`, follow directives (they represent latest decisions)
- If directives are absent or empty, follow `PLAN.md` as-is

#### Outbound — journal to PM layer (append-only)

After completing each implementation step, or when encountering a blocker,
**append** a timestamped entry to `journal.md` in the project root:

```markdown
### {ISO-8601 timestamp} — Step {N}: {short title}
**Status**: ✅ Complete | 🚧 In Progress | ❌ Blocked
**Changes**: {list of files created or modified}
**Next**: {intended next step, referencing PLAN.md}
**Blockers**: {None | description of what needs a PM decision}
```

**Rules:**

- **Never rewrite or delete** existing entries — append only
- Create the file if it does not exist
- Keep entries factual and concise
- Reference `PLAN.md` step numbers for traceability

#### Deliverables Boundary

All code artifacts (source, tests, configs, plans) stay in this repo.
Never write files outside the repo root.
Never write files into `../project-management/`.
