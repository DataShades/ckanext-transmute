from __future__ import annotations
from typing import Callable, Any

import ckan.plugins.toolkit as tk
import ckan.lib.navl.dictization_functions as df

from ckanext.transmute.types import Field

_transmutators: dict[str, Callable[..., Any]] = {}


def get_transmutators():
    return _transmutators


def transmutator(func):
    _transmutators[f"tsm_{func.__name__}"] = func
    return func


@transmutator
def name_validator(field: Field) -> Field:
    """Wrapper over CKAN default `name_validator` validator

    Args:
        field (Field): Field object
    
    Raises:
        df.Invalid: if ``value`` is not a valid name

    Returns:
        Field: the same Field object if it's valid
    """
    name_validator = tk.get_validator("name_validator")
    field.value = name_validator(field.value, {})

    return field


@transmutator
def to_lowercase(field: Field) -> Field:
    """Casts string value to lowercase

    Args:
        field (Field): Field object

    Returns:
        Field: Field object with mutated string
    """
    field.value = field.value.lower()
    return field


@transmutator
def to_uppercase(field: Field) -> Field:
    """Casts string value to uppercase

    Args:
        field (Field): Field object

    Returns:
        Field: Field object with mutated string
    """
    field.value = field.value.upper()
    return field


@transmutator
def string_only(field: Field) -> Field:
    """Validates if field.value is string

    Args:
        value (Field): Field object

    Raises:
        df.Invalid: raises is the field.value is not string

    Returns:
        Field: the same Field object if it's valid
    """
    if not isinstance(field.value, str):
        raise df.Invalid(tk._("Must be a string value"))
    return field


@transmutator
def isodate(field: Field) -> Field:
    """Wrapper over CKAN default `isodate` validator
    Mutates an iso-like string to datetime object

    Args:
        field (Field): Field object

    Raises:
        df.Invalid: raises if date format is incorrect

    Returns:
        Field: the same Field with casted value
    """
    name_validator = tk.get_validator("isodate")
    field.value = name_validator(field.value, {})

    return field


@transmutator
def to_string(field: Field) -> Field:
    field.value = str(field.value)

    return field

@transmutator
def get_nested(field: Field, *path) -> Field:
    for key in path:
        try:
            field.value = field.value[key]
        except TypeError:
            raise df.Invalid(tk._("Error parsing path"))
    
    return field