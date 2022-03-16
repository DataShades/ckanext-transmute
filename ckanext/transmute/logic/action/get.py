from __future__ import annotations

import logging
from re import I
from typing import Any, Callable, Optional

import ckan.plugins.toolkit as tk
import ckan.lib.plugins as lib_plugins
import ckan.lib.navl.dictization_functions as df
from ckan.logic import validate

from ckanext.transmute.types import TransmuteData, Field
from ckanext.transmute.schema import SchemaParser, SchemaField
from ckanext.transmute.schema import transmute_schema, validate_schema
from ckanext.transmute.exception import ValidationError

log = logging.getLogger(__name__)


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
    tk.check_access("tsm_transmute", ctx, data_dict)

    data = data_dict["data"]
    schema = SchemaParser(data_dict["schema"])
    _transmute_data(data, schema)

    return data


def _transmute_data(data, definition, root="Dataset"):
    """Mutates an actual data in `data` dict

    Args:
        data (dict: [str, Any]): a data to mutate
        definition (SchemaParser): SchemaParser object
        root (str): a root schema type
                    the default root is Dataset
    """

    schema = definition.types[root]

    if not schema:
        return
    
    mutate_old_fields(data, definition, root)
    create_new_fields(data, definition, root)


def mutate_old_fields(data, definition, root):
    """Checks all of the data fields and mutate them
    according to the provided schema
    
    New fields won't be created here, because we are
    only traversing the data dictionary
    
    We can't traverse only Data or only Schema, because
    otherwise, the user will have to define all of the fields
    that could exist in data 

    Args:
        data (dict: [str, Any]): a data to mutate
        definition (SchemaParser): SchemaParser object
        root (str): a root schema type
    """
    schema = definition.types[root]
    
    for field_name, value in data.copy().items():
        field: SchemaField = schema["fields"].get(field_name)

        if not field:
            continue

        if field.remove:
            data.pop(field_name)
            continue

        if field.default and not value:
            data[field_name] = value = field.default

        if field.default_from and not value:
            data[field_name] = value = data[field.get_default_from()]

        if field.replace_from:
            data[field_name] = value = data[field.get_replace_from()]

        if field.value:
            if field.update:
                if isinstance(data[field_name], dict):
                    data[field_name].update(field.value)
                elif isinstance(data[field_name], list):
                    data[field_name].extend(field.value)
                else:
                    raise ValidationError({f"{field_name}: the field value is immutable"})
            else:
                data[field_name] = value = field.value

        if field.is_multiple():
            for nested_field in value:
                _transmute_data(nested_field, definition, field.type)
        else:
            data[field_name] = _apply_validators(
                Field(field_name, value, root), field.validators
            )

        if field.map_to:
            data[field.map_to] = data.pop(field_name)


def create_new_fields(data, definition, root):
    """New fields are going to be created according
    to the provided schema
    
    If the defined field is not exist in the data dict
    we are going to create it
    
    The newly created field's value could be inherited from
    an existing field. This field must be defined in the
    schema.
    """
    schema = definition.types[root]
    
    for field_name, field in schema["fields"].items():
        if field_name in data:
            continue
        
        if field.default_from:
            data[field_name] = data[field.get_default_from()]
            
        if field.replace_from:
            data[field_name] = data[field.get_replace_from()]

        if field.value:
            data[field_name] = field.value
        
        if field_name not in data:
            continue

        data[field_name] = _apply_validators(
            Field(field_name, data[field_name], root), field.validators
        )


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
            if isinstance(validator, list):

                # TODO show some error if there are less then 1 arg
                if len(validator) <= 1:
                    pass
                
                tk.get_validator(validator[0])(field, *validator[1:])
            else:
                field = tk.get_validator(validator)(field)
    except df.Invalid as e:
        raise ValidationError({f"{field.type}:{field.field_name}": [e.error]})

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
        package_plugin, ctx, data, schema, 'package_create')

    return data, errors


def _set_package_type(data_dict: dict[str, Any]) -> str:
    """Set a package type

    Args:
        data_dict (dict): package metadata

    Returns:
        str: package type
    """
    if 'type' in data_dict and data_dict['type']:
        return

    package_plugin = lib_plugins.lookup_package_plugin()

    try:
        package_type = package_plugin.package_types()[0]
    except (AttributeError, IndexError):
        package_type = 'dataset'
    
    data_dict["type"] = package_type

def _get_package_schema(ctx):
    package_plugin = lib_plugins.lookup_package_plugin()

    if 'schema' in ctx:
        schema = ctx['schema']
    else:
        schema = package_plugin.create_package_schema()

    return schema