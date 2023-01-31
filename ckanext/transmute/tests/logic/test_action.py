from __future__ import annotations

from typing import Any
from ckanext.transmute.exception import SchemaParsingError, SchemaFieldError

import pytest

import ckan.lib.helpers as h
import ckan.tests.factories as factories
from ckan.logic import ValidationError
from ckan.tests.helpers import call_action

from ckanext.transmute.tests.helpers import build_schema
from ckanext.transmute.types import MODE_FIRST_FILLED


@pytest.mark.ckan_config("ckan.plugins", "scheming_datasets")
class TestTransmuteAction:
    def test_transmute_default(self):
        """If the origin evaluates to False it must be replaced
        with the default value
        """
        data: dict[str, Any] = {
            "metadata_created": "",
        }

        metadata_created_default: str = "2022-02-03"
        tsm_schema = build_schema(
            {
                "metadata_created": {
                    "validators": ["tsm_isodate"],
                    "default": metadata_created_default,
                },
            }
        )

        result = call_action(
            "tsm_transmute",
            data=data,
            schema=tsm_schema,
            root="Dataset",
        )

        assert result["metadata_created"] == h.date_str_to_datetime(
            metadata_created_default
        )

    def test_transmute_default_with_origin_value(self):
        """The default value mustn't replace the origin value"""
        metadata_created: str = "2024-02-03"
        metadata_created_default: str = "2022-02-03"

        data: dict[str, Any] = {
            "metadata_created": metadata_created,
        }

        tsm_schema = build_schema(
            {
                "metadata_created": {
                    "validators": ["tsm_isodate"],
                    "default": metadata_created_default,
                },
            }
        )

        result = call_action(
            "tsm_transmute",
            data=data,
            schema=tsm_schema,
            root="Dataset",
        )

        assert result["metadata_created"] == h.date_str_to_datetime(metadata_created)

    def test_transmute_default_from_without_origin_value(self, tsm_schema):
        """The `default_from` must copy value from target field if the origin
        value is empty
        """
        data: dict[str, Any] = {
            "metadata_created": "",
            "metadata_modified": "",
        }

        result = call_action(
            "tsm_transmute",
            data=data,
            schema=tsm_schema,
            root="Dataset",
        )

        assert result["metadata_created"] == result["metadata_modified"]

    def test_transmute_default_from_with_origin_value(self, tsm_schema):
        """The field value shoudn't be replaced because of `default_from`
        if the value is already exists.
        """
        metadata_modified = "2021-02-03"
        data: dict[str, Any] = {
            "metadata_created": "",
            "metadata_modified": metadata_modified,
        }

        result = call_action(
            "tsm_transmute",
            data=data,
            schema=tsm_schema,
            root="Dataset",
        )

        assert result["metadata_created"] != result["metadata_modified"]
        assert result["metadata_modified"] == h.date_str_to_datetime(metadata_modified)

    def test_transmute_default_from_with_empty_target(self):
        """The target field value could be empty"""
        data: dict[str, Any] = {
            "metadata_created": "",
            "metadata_modified": "",
        }

        tsm_schema = build_schema(
            {
                "metadata_created": {},
                "metadata_modified": {
                    "default_from": "metadata_created",
                },
            }
        )

        result = call_action(
            "tsm_transmute",
            data=data,
            schema=tsm_schema,
            root="Dataset",
        )

        assert result["metadata_created"] == result["metadata_modified"]

    def test_transmute_default_from_without_defining_target_field(self):
        """The field in default_from must be defiend in schema
        Otherwise the SchemaFieldError must be raised
        """
        data: dict[str, Any] = {
            "metadata_created": "",
            "metadata_modified": "",
        }

        target_field: str = "metadata_created"

        tsm_schema = build_schema(
            {
                "metadata_modified": {
                    "default_from": target_field,
                },
            }
        )

        with pytest.raises(SchemaFieldError) as e:
            result = call_action(
                "tsm_transmute",
                data=data,
                schema=tsm_schema,
                root="Dataset",
            )

        assert e.value.error == f"Field: sibling field is not exists: {target_field}"

    def test_transmute_replace_from(self):
        """The `replace_from` must copy value from target field and replace
        the origin value whether it is empty or not
        """
        metadata_created: str = "2024-02-03"
        metadata_modified: str = "2022-02-03"
        data: dict[str, Any] = {
            "metadata_created": metadata_created,
            "metadata_modified": metadata_modified,
        }

        tsm_schema = build_schema(
            {
                "metadata_created": {"validators": ["tsm_isodate"]},
                "metadata_modified": {
                    "replace_from": "metadata_created",
                },
            }
        )

        result = call_action(
            "tsm_transmute",
            data=data,
            schema=tsm_schema,
            root="Dataset",
        )

        assert result["metadata_modified"] == result["metadata_created"]

    def test_transmute_replace_from_multiple(self):
        """Replace from multiple fields must combine values of those fields"""

        data = {"field_1": [1, 2, 3], "field_2": [3, 4, 5], "field_3": ""}

        tsm_schema = build_schema(
            {
                "field_1": {},
                "field_2": {},
                "field_3": {
                    "replace_from": ["field_1", "field_2"],
                },
            }
        )

        result = call_action(
            "tsm_transmute",
            data=data,
            schema=tsm_schema,
            root="Dataset",
        )

        assert result["field_3"] == data["field_1"] + data["field_2"]

    def test_transmute_replace_from_multiple_with_not_existed_one(self):
        """Replace from multiple fields if one of listed field is not exist
        must raise an error"""

        data = {"field_1": [1, 2, 3], "field_2": [3, 4, 5], "field_3": ""}

        tsm_schema = build_schema(
            {
                "field_1": {},
                "field_3": {
                    "replace_from": ["field_1", "field_2"],
                },
            }
        )

        with pytest.raises(SchemaFieldError) as e:
            result = call_action(
                "tsm_transmute",
                data=data,
                schema=tsm_schema,
                root="Dataset",
            )

        assert e.value.error == f"Field: sibling field is not exists: field_2"

    def test_transmute_replace_from_multiple_different_types(self):
        """Replace from multiple fields must combine values of those fields"""

        data = {
            "field_1": [1, 2, 3],
            "field_2": 1,
            "field_3": {"hello": "world"},
            "field_4": "",
        }

        tsm_schema = build_schema(
            {
                "field_1": {},
                "field_2": {},
                "field_3": {},
                "field_4": {
                    "replace_from": ["field_1", "field_2", "field_3"],
                },
            }
        )

        result = call_action(
            "tsm_transmute",
            data=data,
            schema=tsm_schema,
            root="Dataset",
        )

        assert result["field_4"] == data["field_1"] + [data["field_2"]] + [
            data["field_3"]
        ]

    def test_transmute_default_from_multiple(self):
        """Default from multiple fields must combine values of those fields"""

        data = {"field_1": [1, 2, 3], "field_2": [3, 4, 5], "field_3": ""}

        tsm_schema = build_schema(
            {
                "field_1": {},
                "field_2": {},
                "field_3": {
                    "default_from": ["field_1", "field_2"],
                },
            }
        )

        result = call_action(
            "tsm_transmute",
            data=data,
            schema=tsm_schema,
            root="Dataset",
        )

        assert result["field_3"] == data["field_1"] + data["field_2"]

    def test_transmute_default_from_multiple_with_not_existed_one(self):
        """Default from multiple fields if one of listed field is not exist
        must raise an error"""

        data = {"field_1": [1, 2, 3], "field_2": [3, 4, 5], "field_3": ""}

        tsm_schema = build_schema(
            {
                "field_1": {},
                "field_3": {
                    "default_from": ["field_1", "field_2"],
                },
            }
        )

        with pytest.raises(SchemaFieldError) as e:
            result = call_action(
                "tsm_transmute",
                data=data,
                schema=tsm_schema,
                root="Dataset",
            )

        assert e.value.error == f"Field: sibling field is not exists: field_2"

    def test_transmute_default_from_multiple_different_types(self):
        """Default from multiple fields must combine values of those fields"""

        data = {
            "field_1": [1, 2, 3],
            "field_2": 1,
            "field_3": {"hello": "world"},
            "field_4": "",
        }

        tsm_schema = build_schema(
            {
                "field_1": {},
                "field_2": {},
                "field_3": {},
                "field_4": {
                    "default_from": ["field_1", "field_2", "field_3"],
                },
            }
        )

        result = call_action(
            "tsm_transmute",
            data=data,
            schema=tsm_schema,
            root="Dataset",
        )

        assert result["field_4"] == data["field_1"] + [data["field_2"]] + [
            data["field_3"]
        ]

    def test_transmute_replace_from_nested(self):
        data = {
            "title_translated": [
                {"nested_field": {"en": "en title", "ar": "العنوان ar"}},
            ]
        }

        tsm_schema = build_schema(
            {
                "title_translated": {},
                "title": {
                    "replace_from": "title_translated",
                    "validators": [
                        ["tsm_get_nested", 0, "nested_field", "en"],
                        "tsm_to_uppercase",
                    ],
                },
                "title_ar": {
                    "replace_from": "title_translated",
                    "validators": [["tsm_get_nested", 0, "nested_field", "ar"]],
                },
            }
        )

        result = call_action(
            "tsm_transmute",
            data=data,
            schema=tsm_schema,
            root="Dataset",
        )

        result["title"] == data["title_translated"][0]["nested_field"]["en"].upper()
        result["title_ar"] == data["title_translated"][0]["nested_field"]["ar"]

    def test_transmute_remove_field(self):
        """Field with `remove` must be excluded from the result"""
        data: dict[str, Any] = {
            "metadata_created": "2024-02-03",
            "metadata_modified": "2022-02-03",
        }

        tsm_schema = build_schema(
            {
                "metadata_created": {"validators": ["tsm_isodate"]},
                "metadata_modified": {
                    "remove": 1,
                },
            }
        )

        result = call_action(
            "tsm_transmute",
            data=data,
            schema=tsm_schema,
            root="Dataset",
        )

        assert "metadata_modified" not in result

    def test_transmute_value(self):
        """The`value` must replace the origin value, whenever
        it's empty or not"""
        data: dict[str, Any] = {
            "field1": "",
            "field2": "hello-world",
        }

        tsm_schema = build_schema(
            {
                "field1": {"value": 101},
                "field2": {"value": 101},
            }
        )

        result = call_action(
            "tsm_transmute",
            data=data,
            schema=tsm_schema,
            root="Dataset",
        )

        assert result["field1"] == result["field2"] == 101

    def test_transmute_deep_nested(self, tsm_schema):
        data: dict[str, Any] = {
            "title": "Test-dataset",
            "email": "test@test.ua",
            "metadata_created": "",
            "metadata_modified": "",
            "metadata_reviewed": "",
            "resources": [
                {
                    "title": "test-res",
                    "extension": "xml",
                    "web": "https://stackoverflow.com/questions/70167626",
                    "sub-resources": [
                        {
                            "title": "sub-res",
                            "extension": "csv",
                            "extra": "should-be-removed",
                        }
                    ],
                },
                {
                    "title": "test-res2",
                    "extension": "csv",
                    "web": "https://stackoverflow.com/questions/70167626",
                },
            ],
        }

        result = call_action(
            "tsm_transmute",
            data=data,
            schema=tsm_schema,
            root="Dataset",
        )

        metadata_created = h.date_str_to_datetime("2022-02-03T15:54:26.359453")
        assert data == {
            "name": "test-dataset",
            "email": "test@test.ua",
            "metadata_created": metadata_created,
            "metadata_modified": metadata_created,
            "metadata_reviewed": metadata_created,
            "attachments": [
                {
                    "name": "test-res",
                    "format": "XML",
                    "url": "https://stackoverflow.com/questions/70167626",
                    "sub-resources": [{"name": "SUB-RES", "format": "CSV"}],
                },
                {
                    "name": "test-res2",
                    "format": "CSV",
                    "url": "https://stackoverflow.com/questions/70167626",
                },
            ],
        }

    def test_transmute_no_field_schema(self):
        """If no fields specified, there is nothing to do"""
        result = call_action(
            "tsm_transmute",
            data={"title": "test"},
            schema={"root": "Dataset", "types": {"Dataset": {}}},
        )

        assert result == {"title": "test"}

    def test_transmute_no_data(self):
        """Data is required"""
        with pytest.raises(ValidationError):
            call_action(
                "tsm_transmute",
                schema={"root": "Dataset", "types": {"Dataset": {}}},
            )

    def test_transmute_no_schema(self):
        """Schema is required"""
        with pytest.raises(ValidationError):
            call_action("tsm_transmute", data={"title": "test"})

    def test_transmute_empty_data(self):
        """If there is no data, there is no sense to do anything"""
        result = call_action(
            "tsm_transmute",
            data={},
            schema={"root": "Dataset", "types": {"Dataset": {}}},
        )

        assert len(result) == 0

    def test_transmute_empty_schema(self):
        """Schema root type is required"""
        with pytest.raises(SchemaParsingError) as e:
            call_action("tsm_transmute", data={"title": "test"}, schema={})

        assert e.value.error == "Schema: root type is missing"

    def test_transmute_new_field_inherit(self):
        """We can define a new field in schema and it will be
        added to the result data
        """
        data: dict[str, Any] = {
            "metadata_created": "",
        }

        tsm_schema = build_schema(
            {
                "metadata_created": {},
                "metadata_modified": {
                    "default_from": "metadata_created",
                },
            }
        )

        result = call_action(
            "tsm_transmute",
            data=data,
            schema=tsm_schema,
            root="Dataset",
        )

        assert "metadata_modified" in result
        assert result["metadata_modified"] == result["metadata_created"]

    def test_transmute_new_field_from_default_and_value(self):
        """Default runs before value"""
        data: dict[str, Any] = {}

        tsm_schema = build_schema({"field1": {"default": 101, "value": 102}})

        result = call_action(
            "tsm_transmute",
            data=data,
            schema=tsm_schema,
            root="Dataset",
        )

        assert "field1" in result
        assert result["field1"] == 101

    def test_transmute_new_field_from_value(self):
        """We can define a new field in schema and it will be
        added to the result data
        """
        data: dict[str, Any] = {}

        tsm_schema = build_schema({"field1": {"value": 101}})

        result = call_action(
            "tsm_transmute",
            data=data,
            schema=tsm_schema,
            root="Dataset",
        )

        assert "field1" in result
        assert result["field1"] == 101

    def test_transmute_run_multiple_times(self):
        data: dict[str, Any] = {}

        tsm_schema = build_schema({"field1": {"value": 101}})

        for i in range(10):
            result = call_action(
                "tsm_transmute",
                data=data,
                schema=tsm_schema,
                root="Dataset",
            )

        assert "field1" in result
        assert result["field1"] == 101

    def test_transmute_replacing_without_updating(self):
        data: dict[str, Any] = {"extras": [{"key": "test", "value": 0}]}

        extras = [
            {"key": "theme", "value": "nature"},
            {"key": "name", "value": "nature-research"},
        ]
        tsm_schema = build_schema(
            {
                "extras": {"value": extras},
            }
        )

        result = call_action(
            "tsm_transmute",
            data=data,
            schema=tsm_schema,
            root="Dataset",
        )

        assert result["extras"] == extras

    def test_transmute_update_value_list(self):
        data: dict[str, Any] = {"extras": [{"key": "test", "value": 0}]}

        extras = [
            {"key": "theme", "value": "nature"},
            {"key": "name", "value": "nature-research"},
        ]

        tsm_schema = build_schema(
            {
                "extras": {"value": extras, "update": True},
            }
        )

        result = call_action(
            "tsm_transmute",
            data=data,
            schema=tsm_schema,
            root="Dataset",
        )

        assert result["extras"] != extras
        assert len(result["extras"]) == 3

    def test_transmute_update_value_dict(self):
        data: dict[str, Any] = {"extras": {"test1": 1}}

        tsm_schema = build_schema(
            {
                "extras": {"value": {"test2": 2, "test3": 3}, "update": True},
            }
        )

        result = call_action(
            "tsm_transmute",
            data=data,
            schema=tsm_schema,
            root="Dataset",
        )

        assert len(result["extras"]) == 3
        assert "test1" in result["extras"]
        assert "test2" in result["extras"]
        assert "test3" in result["extras"]

    def test_transmute_update_value_immutable(self):
        data: dict[str, Any] = {"resource_number": 101}

        tsm_schema = build_schema(
            {
                "resource_number": {"value": 111, "update": True},
            }
        )

        with pytest.raises(ValidationError) as e:
            call_action(
                "tsm_transmute",
                data=data,
                schema=tsm_schema,
                root="Dataset",
            )

        assert (
            "resource_number: the field value is immutable"
            in e.value.error_dict["message"]
        )

    def test_transmute_update_different_types(self):
        data: dict[str, Any] = {"extras": ["one"]}

        tsm_schema = build_schema(
            {
                "extras": {"value": {"test1": 1}, "update": True},
            }
        )

        with pytest.raises(ValidationError) as e:
            call_action(
                "tsm_transmute",
                data=data,
                schema=tsm_schema,
                root="Dataset",
            )

        assert (
            "extras: the origin value has different type"
            in e.value.error_dict["message"]
        )

    def test_transmute_replace_from_inherit_first_filled_first_true(self):
        """Replace from multiple fields must combine values of those fields"""

        data = {"field_1": [1, 2, 3], "field_2": [3, 4, 5], "field_3": ""}

        tsm_schema = build_schema(
            {
                "field_1": {},
                "field_2": {},
                "field_3": {
                    "replace_from": ["field_1", "field_2"],
                    "inherit_mode": MODE_FIRST_FILLED,
                },
            }
        )

        result = call_action(
            "tsm_transmute",
            data=data,
            schema=tsm_schema,
            root="Dataset",
        )

        assert result["field_3"] == data["field_1"]

    def test_transmute_replace_from_inherit_first_filled_last_true(self):
        """Replace from multiple fields must combine values of those fields"""

        data = {"field_1": "", "field_2": [3, 4, 5], "field_3": ""}

        tsm_schema = build_schema(
            {
                "field_1": {},
                "field_2": {},
                "field_3": {
                    "replace_from": ["field_1", "field_2"],
                    "inherit_mode": MODE_FIRST_FILLED,
                },
            }
        )

        result = call_action(
            "tsm_transmute",
            data=data,
            schema=tsm_schema,
            root="Dataset",
        )

        assert result["field_3"] == data["field_2"]

    def test_transmute_default_from_inherit_first_filled_last_true(self):
        """Replace from multiple fields must combine values of those fields"""

        data = {"field_1": "", "field_2": [3, 4, 5], "field_3": ""}

        tsm_schema = build_schema(
            {
                "field_1": {},
                "field_2": {},
                "field_3": {
                    "default_from": ["field_1", "field_2"],
                    "inherit_mode": MODE_FIRST_FILLED,
                },
            }
        )

        result = call_action(
            "tsm_transmute",
            data=data,
            schema=tsm_schema,
            root="Dataset",
        )

        assert result["field_3"] == data["field_2"]


@pytest.mark.usefixtures("clean_db")
@pytest.mark.ckan_config("ckan.plugins", "scheming_datasets")
class TestValidateAction:
    def test_validate(self):
        dataset = factories.Dataset()

        data_dict = {
            "id": dataset["id"],
            "name": "Test name",
            "private": "1",
            "author_email": "not an email",
        }

        data, errors = call_action(
            "tsm_validate",
            data=data_dict,
        )

        assert len(errors) == 4
