from __future__ import annotations

from typing import Any


def build_schema(fields: dict) -> dict[str, Any]:
    return {"root": "Dataset", "types": {"Dataset": {"fields": fields}}}
