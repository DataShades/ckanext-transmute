from __future__ import annotations

import logging
import contextvars
from typing import Any, Callable, Optional, Union

import ckan.plugins.toolkit as tk
import ckan.lib.plugins as lib_plugins
import ckan.lib.navl.dictization_functions as df
from ckan.logic import validate, ValidationError

from ckanext.transmute.types import TransmuteData, Field, MODE_COMBINE
from ckanext.transmute.schema import SchemaParser, SchemaField
from ckanext.transmute.schema import transmute_schema, validate_schema
from ckanext.transmute.exception import TransmutatorError
from ckanext.transmute.utils import get_transmutator, SENTINEL


log = logging.getLogger(__name__)
data_ctx = contextvars.ContextVar("data")


@tk.side_effect_free
@validate(transmute_schema)
def transmute(ctx: dict[str, Any], data_dict: TransmuteData) -> dict[str, Any]:
    """Transmutes data with the provided convertion scheme
    The function doesn't changes the original data, but creates
    a new data dict.

    Args:
        ctx: CKAN context dict
        data: A data dict to transmute
        schema: schema to transmute data
        root: a root schema type

    Returns:
        Transmuted data dict
    """
    tk.check_access("tsm_transmute", ctx, data_dict)

    data = data_dict["data"]
    data_ctx.set(data)
    schema = SchemaParser(data_dict["schema"])
    _transmute_data(data, schema, data_dict["root"])

    return data


def _transmute_data(data, definition, root):
    """Mutates an actual data in `data` dict

    Args:
        data (dict: [str, Any]): a data to mutate
        definition (SchemaParser): SchemaParser object
        root (str): a root schema type
    """

    schema = definition.types[root]

    if not schema:
        return

    mutate_fields(data, definition, root)


def _weighten_fields(pair: tuple[str, SchemaField]):
    return pair[1].weight


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

    for field_name, field in sorted(schema["fields"].items(), key=_weighten_fields):
        known_fields.add(field_name)

        if field.remove:
            data.pop(field_name, None)
            continue

        value = data.get(field_name)

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
                        {f"{field.name}: the origin value has different type"}
                    )

                if isinstance(data[field.name], dict):
                    data[field.name].update(field.value)
                elif isinstance(data[field.name], list):
                    data[field.name].extend(field.value)
                else:
                    raise ValidationError(
                        {f"{field.name}: the field value is immutable"}
                    )
            else:
                data[field.name] = value = field.value

        if field.is_multiple():
            for nested_field in value or []:
                _transmute_data(nested_field, definition, field.type)

        else:
            if field_name not in data and not field.validate_missing:
                continue

            data[field.name] = _apply_validators(
                Field(field.name, value, root, data_ctx.get()), field.validators
            )

        if field.map:
            known_fields.add(field.map)
            data[field.map] = data.pop(field.name, None)

    if schema.get("drop_unknown_fields"):
        for name in list(data):
            if name not in known_fields:
                del data[name]


def _default_from(data, field: SchemaField):
    default_from: Union[list[str], str] = field.get_default_from()
    return _get_external_fields(data, default_from, field)


def _replace_from(data, field: SchemaField):
    replace_from: Union[list[str], str] = field.get_replace_from()
    return _get_external_fields(data, replace_from, field)


def _get_external_fields(data, external_fields, field: SchemaField):
    if isinstance(external_fields, list):
        if field.inherit_mode == MODE_COMBINE:
            return _combine_from_fields(data, external_fields)
        else:
            return _get_first_filled(data, external_fields)
    return data[external_fields]


def _combine_from_fields(data, external_fields: list[str]):
    value = []

    for field_name in external_fields:
        field_value = data[field_name]

        if isinstance(field_value, list):
            for item in data[field_name]:
                value.append(item)
        else:
            value.append(field_value)

    return value


def _get_first_filled(data, external_fields: list[str]):
    """Return first not-empty field value"""
    for field_name in external_fields:
        field_value = data[field_name]

        if field_value:
            return field_value


def _apply_validators(field: Field, validators: list[str | list[str]]):
    """Applies validators sequentially to the field value

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


@tk.side_effect_free
@validate(validate_schema)
def validate(ctx, data_dict: dict[str, Any]) -> Optional[dict[str, str]]:
    tk.check_access("tsm_transmute", ctx, data_dict)

    data = data_dict["data"]

    _set_package_type(data)
    schema = _get_package_schema(ctx)
    package_plugin = lib_plugins.lookup_package_plugin(data["type"])

    data, errors = lib_plugins.plugin_validate(
        package_plugin, ctx, data, schema, "package_create"
    )

    return data, errors


def _set_package_type(data_dict: dict[str, Any]):
    """Set a package type

    Args:
        data_dict (dict): package metadata

    Returns:
        str: package type
    """
    if "type" in data_dict and data_dict["type"]:
        return

    package_plugin = lib_plugins.lookup_package_plugin()

    try:
        package_type = package_plugin.package_types()[0]
    except (AttributeError, IndexError):
        package_type = "dataset"

    data_dict["type"] = package_type


def _get_package_schema(ctx):
    package_plugin = lib_plugins.lookup_package_plugin()

    if "schema" in ctx:
        schema = ctx["schema"]
    else:
        schema = package_plugin.create_package_schema()

    return schema
