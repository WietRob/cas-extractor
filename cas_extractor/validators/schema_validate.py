"""
Structural Validator — JSON Schema validation for CAS artifacts.
Stage 1 of 2-stage validation.
"""

import json
from pathlib import Path
from typing import Any

import yaml

try:
    import jsonschema
    from jsonschema import Draft202012Validator

    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False


class StructuralValidationResult:
    def __init__(self):
        self.errors: list[dict[str, Any]] = []
        self.warnings: list[dict[str, Any]] = []
        self.files_checked: int = 0
        self.files_valid: int = 0

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def summary(self) -> str:
        status = "PASS" if self.is_valid else "FAIL"
        return (
            f"[{status}] Structural: "
            f"{self.files_valid}/{self.files_checked} valid, "
            f"{len(self.errors)} errors, {len(self.warnings)} warnings"
        )


def validate_structural(
    schemas_dir: str,
    artifacts_dir: str,
) -> StructuralValidationResult:
    if not HAS_JSONSCHEMA:
        result = StructuralValidationResult()
        result.warnings.append(
            {
                "file": "",
                "message": "jsonschema not installed — skipping structural validation",
            }
        )
        return result

    schemas = _load_schemas(schemas_dir)
    result = StructuralValidationResult()

    for yaml_file in sorted(Path(artifacts_dir).rglob("*.yaml")):
        result.files_checked += 1
        try:
            with open(yaml_file, "r") as f:
                data = yaml.safe_load(f)
        except Exception as e:
            result.errors.append(
                {
                    "file": str(yaml_file),
                    "message": f"YAML parse error: {e}",
                }
            )
            continue

        if not isinstance(data, dict):
            result.errors.append(
                {
                    "file": str(yaml_file),
                    "message": "Artifact is not a YAML mapping",
                }
            )
            continue

        kind = data.get("kind")
        schema_key = f"cas.{kind}" if kind else None

        if schema_key and schema_key in schemas:
            schema = schemas[schema_key]
            try:
                store = {}
                for sname, sdata in schemas.items():
                    sid = sdata.get("$id", sname)
                    store[sid] = sdata

                resolver = jsonschema.RefResolver.from_schema(schema, store=store)
                validator = Draft202012Validator(schema, resolver=resolver)
                errors = list(validator.iter_errors(data))

                if errors:
                    for err in errors:
                        result.errors.append(
                            {
                                "file": str(yaml_file),
                                "path": list(err.absolute_path),
                                "message": err.message,
                            }
                        )
                else:
                    result.files_valid += 1

            except Exception as e:
                result.errors.append(
                    {
                        "file": str(yaml_file),
                        "message": f"Validation error: {e}",
                    }
                )
        else:
            result.warnings.append(
                {
                    "file": str(yaml_file),
                    "message": f"No schema found for kind='{kind}'",
                }
            )
            result.files_valid += 1

    return result


def _load_schemas(schemas_dir: str) -> dict[str, Any]:
    schemas = {}
    schemas_path = Path(schemas_dir)

    for schema_file in schemas_path.rglob("*.schema.json"):
        try:
            with open(schema_file, "r") as f:
                schema = json.load(f)
            name = schema_file.stem.replace(".v0.1.schema", "")
            schemas[name] = schema
        except Exception:
            continue

    return schemas
