# Benchmark Framework

Generic benchmark framework for comparing iterative solutions — algorithmic approaches and/or hyperparameter variants.

## Quick Start

```bash
# Install dependencies
make setup

# Run tests
make test

# Run the demo benchmark
make benchmark-demo
```

## Overview

This framework provides:

- **JSON-based configuration** for iterations, metrics, runs, and results
- **Pluggable metric classes** via dynamic Python class loading
- **Sequential benchmark runner** that executes iterations × metrics
- **Markdown report generator** with comparison tables and narrative

## Usage

```python
from benchmark_framework.api import execute_run, generate_report

# Execute a benchmark run
execute_run(run_id="run-001", config_dir="path/to/config/")

# Generate comparison report
generate_report(config_dir="path/to/config/", output_path="report.md")
```

## Configuration Files

| File | Purpose |
|------|---------|
| `iterations.json` | Registry of solution variants to benchmark |
| `metrics.json` | Definitions of measurements and their Python classes |
| `runs.json` | Run definitions: which iterations × which metrics |
| `results.json` | Append-only results from executed runs |

See `schemas/` for JSON Schema definitions.

## License

MIT
