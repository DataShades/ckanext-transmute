from __future__ import annotations

from typing import Any, Callable, Optional

import ckan.plugins.toolkit as tk
import ckan.lib.navl.dictization_functions as df
from ckan.logic import validate

from ckanext.transmute.types import TransmuteData, Field
from ckanext.transmute.schema import SchemaParser, transmute_schema, SchemaField
from ckanext.transmute.exception import ValidationError


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

    Returns:
        Transmuted data dict
    """
    tk.check_access("tsm_get_schemas", ctx, data_dict)

    data = data_dict["data"]
    schema = SchemaParser(data_dict["schema"])
    _mutate_data(data, schema, "Dataset")

    return data


def _mutate_data(data, definition, root):
    """Mutates an actual data in `data` dict

    Args:
        data (dict: [str, Any]): a data to mutate
        definition (SchemaParser): SchemaParser object
        root (str): a root schema type
    """

    schema = definition.types[root]

    if not schema:
        return

    for field, value in data.copy().items():
        schema_field: SchemaField = schema["fields"].get(field)

        if not schema_field:
            continue

        if schema_field.remove:
            data.pop(field)
            continue

        if schema_field.default and not value:
            data[field] = schema_field.default

        if schema_field.default_from and not value:
            data[field] = data[schema_field.get_default_from()]

        if schema_field.replace_from:
            data[field] = data[schema_field.get_replace_from()]

        if schema_field.is_multiple():
            for nested_field in value:
                _mutate_data(nested_field, definition, schema_field.type)
        else:
            data[field] = _apply_validators(
                Field(field, value or data[field], root), schema_field.validators
            )

        if schema_field.map_to:
            data[schema_field.map_to] = data.pop(field)


def _apply_validators(field: Field, validators: list[Callable[[Field], Any]]):
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
            field = tk.get_validator(validator)(field)
    except df.Invalid as e:
        raise ValidationError({f"{field.type}:{field.field_name}": [e.error]})

    return field.value


@tk.side_effect_free
def validate(ctx, data_dict) -> Optional[dict[str, str]]:
    pass
