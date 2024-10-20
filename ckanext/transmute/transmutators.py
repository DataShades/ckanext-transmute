from __future__ import annotations
from typing import Callable, Any, Optional
from datetime import datetime

from dateutil.parser import parse, ParserError

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
    """Validates datetime string
    Mutates an iso-like string to datetime object

    Args:
        field (Field): Field object

    Raises:
        df.Invalid: raises if date format is incorrect

    Returns:
        Field: the same Field with casted value
    """

    if isinstance(field.value, datetime):
        return field

    try:
        field.value = parse(field.value)
    except ParserError:
        raise df.Invalid(tk._("Date format incorrect"))

    return field


@transmutator
def to_string(field: Field) -> Field:
    """Casts field.value to str

    Args:
        field (Field): Field object

    Returns:
        Field: the same Field with new value
    """
    field.value = str(field.value)

    return field


@transmutator
def stop_on_empty(field: Field) -> Field:
    """Stop transmutation if field is empty

    Args:
        field (Field): Field object

    Returns:
        Field: the same Field
    """
    if not field.value:
        raise df.StopOnError

    return field


@transmutator
def get_nested(field: Field, *path) -> Field:
    """Fetches a nested value from a field

    Args:
        field (Field): Field object

    Raises:
        df.Invalid: raises if path doesn't exist

    Returns:
        Field: the same Field with new value
    """
    for key in path:
        try:
            field.value = field.value[key]
        except TypeError:
            raise df.Invalid(tk._("Error parsing path"))
    return field


@transmutator
def trim_string(field: Field, max_length) -> Field:
    """Trim string lenght

    Args:
        value (Field): Field object
        max_length (int): String max length

    Returns:
        Field: the same Field object if it's valid
    """

    if not isinstance(max_length, int):
        raise df.Invalid(tk._("max_length must be integer"))

    field.value = field.value[:max_length]
    return field


@transmutator
def concat(field: Field, *strings) -> Field:
    """Concat strings to build a new one
    Use $self to point on field value

    Args:
        field (Field): Field object
        *strings (tuple[str]): strings to concat with

    Returns:
        Field: the same Field with new value
    """
    if not strings:
        raise df.Invalid(tk._("No arguments for concat"))

    value_chunks = []

    for s in strings:
        if s == "$self":
            value_chunks.append(field.value)
        elif isinstance(s, str) and s.startswith("$"):
            ref_field_name: str = s.lstrip("$").strip()

            if ref_field_name not in field.data:
                continue

            value_chunks.append(field.data[ref_field_name])
        else:
            value_chunks.append(s)

    field.value = "".join(str(s) for s in value_chunks)

    return field


@transmutator
def unique_only(field: Field) -> Field:
    """Preserve only unique values from list

    Args:
        field (Field): Field object

    Returns:
        Field: the same Field with new value
    """
    if not isinstance(field.value, list):
        raise df.Invalid(tk._("Field value must be an array"))
    field.value = list(set(field.value))
    return field


@transmutator
def mapper(
    field: Field, mapping: dict[Any, Any], default: Optional[Any] = None
) -> Field:
    """Map a value with a new value. The initial value must serve as a key within
    a mapping dictionary, while the dict value will represent the updated value.

    Args:
        field (Field): Field object
        mapping (dict[Any, Any]): A dictionary representing the mapping of values.
        default (Any): The default value to be used when the key is not found in the mapping.
            If the default value is not provided, the current value will be used as it.

    Returns:
        Field: the same Field with new value
    """
    new_value = mapping.get(field.value, default or field.value)

    field.value = new_value

    return field


@transmutator
def list_mapper(
    field: Field,
    mapping: dict[Any, Any],
    remove: Optional[bool] = False,
) -> Field:
    """
    Maps values within a list to their corresponding values in a provided mapping dictionary.

    Args:
        field (Field): Field object
        mapping (dict[Any, Any]): A dictionary representing the mapping of values.
        remove (bool, optional): If set to True, removes values from the list if
            they don't have a corresponding mapping. Defaults to False.
    """
    if not isinstance(field.value, list):
        return field

    result = []

    for value in field.value:
        map_value = mapping.get(value)

        if not map_value and remove:
            continue

        result.append(map_value or value)

    field.value = result

    return field
