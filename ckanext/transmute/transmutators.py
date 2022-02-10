from __future__ import annotations
from typing import Callable, Any


_transmutators: dict[str, Callable[..., Any]] = {}


def get_transmutators():
    return _transmutators


def transmutator(func):
    _transmutators[f"tsm_{func.__name__}"] = func
    return func
