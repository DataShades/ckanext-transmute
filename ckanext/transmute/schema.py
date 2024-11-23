from __future__ import annotations

import copy
import dataclasses
from typing import Any

from ckan import types
from ckan.logic.schema import validator_args

from ckanext.transmute.exception import SchemaFieldError, SchemaParsingError
from ckanext.transmute.utils import SENTINEL


@dataclasses.dataclass
class SchemaField:
    name: str
    type: str
    definition: dict[str, Any]
    map: str | None = None
    validators: list[Any] = dataclasses.field(default_factory=list)
    multiple: bool = False
    remove: bool = False
    default: Any = SENTINEL
    default_from: str | None = None
    value: Any = SENTINEL
    replace_from: str | None = None
    inherit_mode: str | None = "combine"
    update: bool = False
    validate_missing: bool = False
    weight: int = 0

    def __repr__(self):
        return (
            f"<Field name={self.name} map={self.map}"
            f" type={self.type} multiple={self.multiple}"
            f" validators={self.validators}>"
        )

    def is_multiple(self) -> bool:
        return bool(self.multiple)

    def get_default_from(self) -> list[str] | str:
        if not self.default_from:
            raise SchemaFieldError("Field: `default_from` field name is not defined")

        if isinstance(self.default_from, list):
            return [
                self._get_sibling_field_name(field_name)
                for field_name in self.default_from
            ]

        return self._get_sibling_field_name(self.default_from)

    def get_replace_from(self) -> list[str] | str:
        if not self.replace_from:
            raise SchemaFieldError("Field: `replace_from` field name is not defined")

        if isinstance(self.replace_from, list):
            return [
                self._get_sibling_field_name(field_name)
                for field_name in self.replace_from
            ]

        return self._get_sibling_field_name(self.replace_from)

    def _get_sibling_field_name(self, field_name: str) -> str:
        return field_name


class SchemaParser:
    def __init__(self, schema: dict[str, Any]):
        self.schema = copy.deepcopy(schema)
        self.root_type = self.get_root_type()
        self.types = self.parse_types()
        self.parse_fields("pre-fields")
        self.parse_fields("fields")
        self.parse_fields("post-fields")

    def get_root_type(self):
        root_type: str = self.schema.get("root", "")

        if not root_type:
            raise SchemaParsingError("Schema: root type is missing")

        if root_type not in self.schema.get("types", []):
            raise SchemaParsingError("Schema: root_type is declared but not defined")

        return root_type

    def parse_types(self):
        if not self.schema.get("types"):
            raise SchemaParsingError("Schema: types are missing")

        return self.schema["types"]

    def parse_fields(self, field_type: str):
        for _type, type_meta in self.types.items():
            for field_name, field_meta in type_meta.setdefault(field_type, {}).items():
                type_meta[field_type][field_name] = self._parse_field(
                    field_name, field_meta, _type
                )

    def _parse_field(
        self, field_name: str, field_meta: dict[str, Any], _type: str
    ) -> SchemaField:
        """Create a SchemaField combining all the
        information about field.

        Args:
            field_name (str): current field original name
            field_meta (dict): field definition from parent type
            _type (str): parent type

        Returns:
            SchemaField: SchemaField object
        """
        params: dict[str, Any] = dict({"type": _type}, **field_meta)
        return SchemaField(name=field_name, definition=self.types[_type], **params)


@validator_args
def transmute_schema(
    not_missing: types.Validator,
    default: types.ValidatorFactory,
) -> types.Schema:
    return {
        "data": [not_missing],
        "schema": [not_missing],
        "root": [default("Dataset")],
    }


@validator_args
def validate_schema(not_missing: types.Validator) -> types.Schema:
    return {
        "data": [not_missing],
    }
