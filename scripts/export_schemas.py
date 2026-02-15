"""Export JSON schemas from Pydantic models to schemas/ directory."""

import json
from pathlib import Path

from benchmark_framework.models import (
    IterationsConfig,
    MetricsConfig,
    ResultsConfig,
    RunsConfig,
)

SCHEMAS_DIR = Path(__file__).parent.parent / "schemas"


def export_schemas() -> None:
    """Export all JSON schemas to the schemas/ directory."""
    SCHEMAS_DIR.mkdir(exist_ok=True)

    schemas = {
        "iterations.schema.json": IterationsConfig,
        "metrics.schema.json": MetricsConfig,
        "runs.schema.json": RunsConfig,
        "results.schema.json": ResultsConfig,
    }

    for filename, model in schemas.items():
        schema = model.model_json_schema()
        path = SCHEMAS_DIR / filename
        path.write_text(json.dumps(schema, indent=2) + "\n")
        print(f"Exported {path}")


if __name__ == "__main__":
    export_schemas()
