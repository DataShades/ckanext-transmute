from __future__ import annotations

from typing import Any, Optional, Union

import copy

from ckan.logic.schema import validator_args

from ckanext.transmute.exception import SchemaParsingError, SchemaFieldError


class SchemaField:
    def __init__(
        self,
        *,
        name: str,
        type_: str,
        definition: dict,
        map_to: Optional[str] = None,
        validators: Optional[list] = None,
        multiple: bool = False,
        remove: bool = False,
        default: Optional[Any] = None,
        default_from: Optional[str] = None,
        value: Optional[Any] = None,
        replace_from: Optional[str] = None,
        inherit_mode: Optional[str] = None,
        update: bool = False,
    ):
        self.name = name
        self.type = type_
        self.definition = definition
        self.map_to = map_to
        self.validators = validators or []
        self.multiple = multiple
        self.remove = remove
        self.default = default
        self.default_from = default_from
        self.replace_from = replace_from
        self.inherit_mode = inherit_mode
        self.value = value
        self.update = update

    def __repr__(self):
        return (
            f"<Field name={self.name} map_to={self.map_to}"
            f" type={self.type} multiple={self.multiple}"
            f" validators={self.validators}>"
        )

    def is_multiple(self) -> bool:
        return bool(self.multiple)

    def get_default_from(self) -> Union[list[str], str]:
        if not self.default_from:
            raise SchemaFieldError("Field: `default_from` field name is not defined")

        if isinstance(self.default_from, list):
            return [
                self._get_sibling_field_name(field_name)
                for field_name in self.default_from
            ]

        return self._get_sibling_field_name(self.default_from)

    def get_replace_from(self) -> Union[list[str], str]:
        if not self.replace_from:
            raise SchemaFieldError("Field: `replace_from` field name is not defined")

        if isinstance(self.replace_from, list):
            return [
                self._get_sibling_field_name(field_name)
                for field_name in self.replace_from
            ]

        return self._get_sibling_field_name(self.replace_from)

    def _get_sibling_field_name(self, field_name: str) -> Optional[Any]:
        field = self.definition["fields"].get(field_name)

        if not field:
            raise SchemaFieldError(f"Field: sibling field is not exists: {field_name}")

        return field_name


class SchemaParser:
    def __init__(self, schema):
        self.schema = copy.deepcopy(schema)
        self.root_type = self.get_root_type()
        self.types = self.parse_types()
        self.parse_fields()

    def get_root_type(self):
        root_type: str = self.schema.get("root")

        if not root_type:
            raise SchemaParsingError("Schema: root type is missing")

        if not root_type in self.schema.get("types"):
            raise SchemaParsingError("Schema: root_type is declared but not defined")

        return root_type

    def parse_types(self):
        if not self.schema.get("types"):
            raise SchemaParsingError("Schema: types are missing")

        return self.schema["types"]

    def parse_fields(self):
        for _type, type_meta in self.types.items():
            for field_name, field_meta in type_meta.get("fields", {}).items():
                type_meta["fields"][field_name] = self._parse_field(
                    field_name, field_meta, _type
                )

    def _parse_field(
        self, field_name: str, field_meta: dict, _type: str
    ) -> SchemaField:
        """Create a SchemaField combining all the
        information about field

        Args:
            field_name (str): current field original name
            field_meta (dict): field definition from parent type
            _type (str): parent type

        Returns:
            SchemaField: SchemaField object
        """

        return SchemaField(
            name=field_name,
            type_=field_meta.get("type", _type),
            definition=self.types[_type],
            map_to=field_meta.get("map", None),
            validators=field_meta.get("validators"),
            multiple=field_meta.get("multiple", False),
            remove=field_meta.get("remove", False),
            default=field_meta.get("default", None),
            default_from=field_meta.get("default_from", None),
            value=field_meta.get("value", None),
            replace_from=field_meta.get("replace_from", None),
            inherit_mode=field_meta.get("inherit_mode", "combine"),
            update=field_meta.get("update", False),
        )


@validator_args
def transmute_schema(not_missing):
    return {
        "data": [not_missing],
        "schema": [not_missing],
    }


@validator_args
def validate_schema(not_missing):
    return {
        "data": [not_missing],
    }
