from typing import Any, Optional

from ckan.logic.schema import validator_args

from ckanext.transmute.exception import SchemaParsingError, SchemaFieldError


class SchemaField:
    def __init__(
        self,
        name: str,
        type_: str,
        definition: dict,
        map_to: Optional[str],
        validators: Optional[list],
        multiple: bool,
        remove: bool,
        default: Optional[Any],
        default_from: Optional[str],
        replace_from: Optional[str],
        replace_with: Optional[Any]
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
        self.replace_with = replace_with

    def __repr__(self):
        return (f"<Field name={self.name} map_to={self.map_to}"
                f" type={self.type} multiple={self.multiple}"
                f" validators={self.validators}>")

    def is_multiple(self) -> bool:
        return self.multiple
    
    def get_default_from(self) -> Optional[Any]:
        if not self.default_from:
            raise SchemaFieldError("Field: `default_from` field is not defined")
        return self._get_sibling_field_value(self.default_from)
    
    def get_replace_from(self) -> Optional[Any]:
        if not self.replace_from:
            raise SchemaFieldError("Field: `replace_from` field is not defined")
        return self._get_sibling_field_value(self.replace_from)

    def _get_sibling_field_value(self, field_name: str) -> Optional[Any]:
        return self.definition["field"].get(field_name)

class SchemaParser:
    def __init__(self, schema):
        self.schema = schema
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
            field_name,
            field_meta.get("type", _type),
            self.types[_type],
            field_meta.get("map", None),
            field_meta.get("validators"),
            field_meta.get("multiple", False),
            field_meta.get("remove", False),
            field_meta.get("default", None),
            field_meta.get("default_from", None),
            field_meta.get("replace_with", None),
            field_meta.get("replace_from", None)
        )


@validator_args
def transmute_schema(not_missing):

    return {
        "data": [not_missing],
        "schema": [not_missing],
    }
