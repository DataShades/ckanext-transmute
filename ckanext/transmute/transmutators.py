from __future__ import annotations

from datetime import datetime
from typing import Any, Callable

from dateutil.parser import ParserError, parse

import ckan.lib.navl.dictization_functions as df
import ckan.plugins.toolkit as tk

from ckanext.transmute.types import Field

SENTINEL = object()


def get_transmutators():
    return {
        "tsm_name_validator": tsm_name_validator,
        "tsm_to_lowercase": tsm_to_lowercase,
        "tsm_to_uppercase": tsm_to_uppercase,
        "tsm_string_only": tsm_string_only,
        "tsm_isodate": tsm_isodate,
        "tsm_to_string": tsm_to_string,
        "tsm_stop_on_empty": tsm_stop_on_empty,
        "tsm_get_nested": tsm_get_nested,
        "tsm_trim_string": tsm_trim_string,
        "tsm_concat": tsm_concat,
        "tsm_unique_only": tsm_unique_only,
        "tsm_mapper": tsm_mapper,
        "tsm_list_mapper": tsm_list_mapper,
        "tsm_map_value": tsm_map_value,
    }


def tsm_name_validator(field: Field) -> Field:
    """Wrapper over CKAN default `name_validator` validator.

    Example:
        Raise an error for `NOT A VALID NAME`, but accept `not-a-valid-name`.
        ```json
        {"validators": ["tsm_name_validator"]}
        ```

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


def tsm_to_lowercase(field: Field) -> Field:
    """Casts string value to lowercase.

    Example:
        Transform `HeLlO` to `hello`.
        ```json
        {"validators": ["tsm_to_lowercase"]}
        ```

    Args:
        field (Field): Field object

    Returns:
        Field: Field object with mutated string
    """
    field.value = field.value.lower()
    return field


def tsm_to_uppercase(field: Field) -> Field:
    """Casts string value to uppercase.

    Example:
        Transform `HeLlO` to `HELLO`.
        ```json
        {"validators": ["tsm_to_uppercase"]}
        ```

    Args:
        field (Field): Field object

    Returns:
        Field: Field object with mutated string
    """
    field.value = field.value.upper()
    return field


def tsm_string_only(field: Field) -> Field:
    """Validates if `field.value` is string.

    Example:
        Raise an error for `1` but accept `"1"`.
        ```json
        {"validators": ["tsm_string_only"]}
        ```

    Args:
        field (Field): Field object

    Raises:
        df.Invalid: raises is the `field.value` is not string

    Returns:
        Field: the same Field object if it's valid
    """
    if not isinstance(field.value, str):
        raise df.Invalid(tk._("Must be a string value"))
    return field


def tsm_isodate(field: Field) -> Field:
    """Validates datetime string
    Mutates an iso-like string to datetime object.

    Example:
        Transform `"2022-01-01"` into `datetime(year=2022, month=1, day=1)`.
        ```json
        {"validators": ["tsm_isodate"]}
        ```

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


def tsm_to_string(field: Field) -> Field:
    """Casts `field.value` to str.

    Example:
        Transform `[1, 2, 3]` into string `"[1, 2, 3]"`. Note, that `null` as
        missing value will turn into string `"None"`.

        ```json
        {"validators": ["tsm_to_string"]}
        ```

    Args:
        field (Field): Field object

    Returns:
        Field: the same Field with new value

    """
    field.value = str(field.value)

    return field


def tsm_stop_on_empty(field: Field) -> Field:
    """Stop transmutation if field is empty.

    Example:
        Accept the current value and do not call the rest of transmutators if
        value is represented by falsy object(0, null, empty string, empty list,
        etc.)

        ```json
        {"validators": [
            "tsm_stop_on_empty",
            "i_am_called_with_nonempty_values_only"
        ]}

        {"validators": [
            "tsm_to_string",
            "tsm_stop_on_empty",
            "only_nonempty_strings_come_here"
        ]}
        ```

    Args:
        field (Field): Field object

    Returns:
        Field: the same Field

    """
    if not field.value:
        raise df.StopOnError

    return field


def tsm_get_nested(field: Field, *path: str) -> Field:
    """Fetches a nested value from a field.

    Example:
        Assuming `field.value` contains `{"a": {"b": [1, 2, 3]}}`, extract
        element with key `a`, from it take element with key `b`, than get the
        element with index `1`. In the end, value is replaced by `2`.

        ```json
        {"validators": [
            ["tsm_get_nested", "a", "b", "1"]
        ]}
        ```

    Args:
        field (Field): Field object
        path: Iterable with path segments

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


def tsm_trim_string(field: Field, max_length: int) -> Field:
    """Trim string lenght.

    Example:
        Keep only first 5 characters in the `hello world`, turning it into
        `hello`.

        ```json
        {"validators": [
            ["tsm_trim_string", 5]
        ]}
        ```

    Args:
        field (Field): Field object
        max_length (int): String max length

    Returns:
        Field: the same Field object if it's valid

    """
    if not isinstance(max_length, int):
        raise df.Invalid(tk._("max_length must be integer"))

    field.value = field.value[:max_length]
    return field


def tsm_concat(field: Field, *strings: Any) -> Field:
    """Concatenate strings to build a new one.

    Example:
        Greet the value in form `Hello VALUE!`.

        ```json
        {"validators": [
            ["tsm_concat", "Hello ", "$self", "!"]
        ]}
        ```

    Args:
        field: Field object
        strings: strings to concat with

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


def tsm_unique_only(field: Field) -> Field:
    """Preserve only unique values from list.

    Example:
        Remove duplicates from `[1, 1, 2, 1, 2, 2, 1, 3]`, keeping `[1, 2, 3]`.

        ```json
        {"validators": ["tsm_unique_only"]}
        ```

    Args:
        field (Field): Field object

    Returns:
        Field: the same Field with new value

    """
    if not isinstance(field.value, list):
        raise df.Invalid(tk._("Field value must be an array"))
    field.value = list(set(field.value))
    return field


def tsm_mapper(
    field: Field, mapping: dict[Any, Any], default: Any | None = None
) -> Field:
    """Replace a value with a different value.

    The initial value must serve as a key within a mapping dictionary, while
    the dict value will represent the updated value.

    Example:
        Replace `Finn` with `human`, and `Jake` with `dog`.

        ```json
        {"validators": [
            ["tsm_mapper", {"Finn": "human", "Jake": "dog"}]
        ]}
        ```

    Args:
        field (Field): Field object
        mapping (dict[Any, Any]): A dictionary representing the mapping of values.
        default (Any): The default value to be used when the key is not found.
            If the default value is not provided, the current value will be used as it.

    Returns:
        Field: the same Field with new value

    """
    new_value = mapping.get(field.value, default or field.value)

    field.value = new_value

    return field


def tsm_list_mapper(
    field: Field,
    mapping: dict[Any, Any],
    remove: bool | None = False,
) -> Field:
    """Maps values within a list to corresponding values from the provided dictionary.

    Example:
        Replace `["Finn", "Jake"]` with `["human", "dog"]`.

        ```json
        {"validators": [
            ["tsm_list_mapper", {"Finn": "human", "Jake": "dog"}]
        ]}
        ```

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


def tsm_map_value(
    field: Field,
    test_value: Any,
    if_same: Any,
    if_different: Any = SENTINEL,
) -> Field:
    """Replace special value with other value.

    Example:
        Replace `me` with `COOL USER`, and any other value with `user`.

        ```json
        {"validators": [
            ["tsm_map_value", "me", "COOL USER", "user"]
        ]}
        ```

    Args:
        field: Field object
        test_value: value that will be compared to `field.value`
        if_same: value to use if test_value matches the `field.value`
        if_different: value to use if test_value does not matche the `field.value`.
            Leave empty to keep original value of the field.
    """
    if field.value == test_value:
        field.value = if_same

    elif if_different is not SENTINEL:
        field.value = if_different

    return field
