from __future__ import annotations

import dataclasses
from typing import Any
from typing_extensions import TypedDict


class TransmuteData(TypedDict):
    data: dict[str, Any]
    schema: dict[str, Any]
    root: str


@dataclasses.dataclass
class Field:
    field_name: str
    value: Any
    type: str
    data: dict[str, Any]


MODE_COMBINE = "combine"
MODE_FIRST_FILLED = "first-filled"
