from __future__ import annotations

import contextvars
import logging
from typing import Any

import ckan.lib.navl.dictization_functions as df
import ckan.plugins.toolkit as tk
from ckan import types
from ckan.logic import ValidationError, validate

from ckanext.transmute.exception import TransmutatorError
from ckanext.transmute.schema import SchemaField, SchemaParser, transmute_schema
from ckanext.transmute.types import MODE_COMBINE, Field
from ckanext.transmute.utils import SENTINEL, get_schema, get_transmutator

log = logging.getLogger(__name__)
data_ctx = contextvars.ContextVar("data")


def get_actions():
    return {
        "tsm_transmute": tsm_transmute,
    }


@tk.side_effect_free
@validate(transmute_schema)
def tsm_transmute(context: types.Context, data_dict: dict[str, Any]) -> dict[str, Any]:
    """Transmute data using the schema.

    The function creates a deep copy of the data and performs all modifications
    on the copy.

    Args:
        data (dict[str, Any]): A data dict to transmute
        schema (dict[str, Any]): schema to transmute data
        root (str): a root schema type

    Returns:
        Transmuted data

    """
    tk.check_access("tsm_transmute", context, data_dict)

    data = data_dict["data"]
    data_ctx.set(data)

    schema: dict[str, Any] | str = data_dict["schema"]
    if isinstance(schema, str):
        schema = get_schema(schema) or {}

    definition = SchemaParser(schema)
    _transmute_data(data, definition, data_dict["root"])

    return data


def _transmute_data(data, definition, root):
    """Mutates an actual data in `data` dict.

    Args:
        data (dict: [str, Any]): a data to mutate
        definition (SchemaParser): SchemaParser object
        root (str): a root schema type
    """
    schema = definition.types[root]

    if not schema:
        return

    mutate_fields(data, definition, root)


def _weighten_fields(field: SchemaField):
    return field.weight


def mutate_fields(data: dict[str, Any], definition: SchemaParser, root: str):
    """Checks all of the schema fields and mutate/create them according to the
    provided schema.

    Args:
        data (dict: [str, Any]): a data to mutate
        definition (SchemaParser): SchemaParser object
        root (str): a root schema type

    """
    schema = definition.types[root]

    known_fields: set[str] = set()

    for field in sorted(schema["pre-fields"].values(), key=_weighten_fields):
        _process_field(field, data, definition)

    for field in sorted(schema["fields"].values(), key=_weighten_fields):
        name = _process_field(field, data, definition)
        if name:
            known_fields.add(name)

    for field in sorted(schema["post-fields"].values(), key=_weighten_fields):
        _process_field(field, data, definition)

    if schema.get("drop_unknown_fields"):
        for name in list(data):
            if name not in known_fields:
                del data[name]


def _process_field(
    field: SchemaField, data: dict[str, Any], definition: SchemaParser
) -> str | None:
    if field.remove:
        data.pop(field.name, None)
        return

    value: Any = data.get(field.name)

    if field.default_from and not value:
        data[field.name] = value = _default_from(data, field)

    if field.replace_from:
        data[field.name] = value = _replace_from(data, field)

    # set static default **after** attempt to get default from the other field
    if field.default is not SENTINEL and not value:
        data[field.name] = value = field.default

    if field.value is not SENTINEL:
        if field.update:
            if not isinstance(data[field.name], type(field.value)):
                raise ValidationError(
                    {field.name: ["Original value has different type"]}
                )

            if isinstance(data[field.name], dict):
                data[field.name].update(field.value)
            elif isinstance(data[field.name], list):
                data[field.name].extend(field.value)
            else:
                raise ValidationError({field.name: ["Field value is not mutable"]})
        else:
            data[field.name] = value = field.value


    if field.is_multiple():
        for nested_field in value or []:  # type: ignore
            _transmute_data(nested_field, definition, field.type)

    else:
        if field.name not in data and not field.validate_missing:
            return

        data[field.name] = _apply_validators(
            Field(field.name, value, field.type, data_ctx.get()), field.validators
        )

    if field.map:
        data[field.map] = data.pop(field.name, None)
        return field.map

    return field.name


def _default_from(data: dict[str, Any], field: SchemaField):
    default_from: list[str] | str = field.get_default_from()
    return _get_external_fields(data, default_from, field)


def _replace_from(data: dict[str, Any], field: SchemaField):
    replace_from: list[str] | str = field.get_replace_from()
    return _get_external_fields(data, replace_from, field)


def _get_external_fields(
    data: dict[str, Any], external_fields: Any, field: SchemaField
):
    if isinstance(external_fields, list):
        if field.inherit_mode == MODE_COMBINE:
            return _combine_from_fields(data, external_fields)
        else:
            return _get_first_filled(data, external_fields)
    return data[external_fields]


def _combine_from_fields(data: dict[str, Any], external_fields: list[str]):
    value: list[Any] = []

    for field_name in external_fields:
        field_value = data[field_name]

        if isinstance(field_value, list):
            for item in data[field_name]:
                value.append(item)
        else:
            value.append(field_value)

    return value


def _get_first_filled(data: dict[str, Any], external_fields: list[str]):
    """Return first not-empty field value."""
    for field_name in external_fields:
        field_value = data[field_name]

        if field_value:
            return field_value


def _apply_validators(field: Field, validators: list[str | list[str]]):
    """Applies validators sequentially to the field value.

    Args:
        field (Field): Field object
        validators (list[Callable[[Field], Any]]): a list of
            validators functions. Validator could just validate data
            or mutate it.

    Raises:
        ValidationError: raises a validation error

    Returns:
        Field.value: the value that passed through
            the validators sequence. Could be changed.
    """
    try:
        for validator in validators:
            if isinstance(validator, list):
                if len(validator) <= 1:
                    raise TransmutatorError("Arguments for validator weren't provided")
                field = get_transmutator(validator[0])(field, *validator[1:])
            else:
                field = get_transmutator(validator)(field)
    except df.StopOnError:
        return field.value
    except df.Invalid as e:
        raise ValidationError({f"{field.type}:{field.field_name}": [e.error]})
    except TypeError as e:
        raise TransmutatorError(str(e))

    return field.value
