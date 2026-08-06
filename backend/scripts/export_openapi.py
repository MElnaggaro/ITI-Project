"""Script to export OpenAPI specification to openapi.json in repo root."""

import json
import os
import sys
from pathlib import Path

# Ensure project root is on sys.path for direct script executions
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def export_openapi() -> None:
    """Generate and write openapi.json using FastAPI application schema."""
    os.environ["APP_ENVIRONMENT"] = "test"
    from app.main import app


    output_path = Path(__file__).resolve().parent.parent / "openapi.json"
    schema = app.openapi()
    output_path.write_text(json.dumps(schema, indent=2), encoding="utf-8")
    print(f"Exported OpenAPI schema to {output_path}")


if __name__ == "__main__":
    export_openapi()
