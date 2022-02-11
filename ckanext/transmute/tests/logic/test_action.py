from __future__ import annotations

from typing import Any
from ckanext.transmute.exception import SchemaParsingError, SchemaFieldError

import pytest

import ckan.lib.helpers as h
import ckan.logic as logic
from ckan.tests.helpers import call_action

from ckanext.transmute.tests.helpers import build_schema


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
        """The default value mustn't replace the origin value
        """
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

        result["metadata_created"] == h.date_str_to_datetime("2022-02-03")

    def test_transmute_default_from_without_origin_value(self, tsm_schema):
        """The `default_from` must copy value from target field if the origin
        value is empty
        """
        data: dict[str, Any] = {
            "title": "Test-dataset",
            "email": "test@test.ua",
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
            "title": "Test-dataset",
            "email": "test@test.ua",
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
        """The target field value could be empty
        """
        data: dict[str, Any] = {
            "title": "Test-dataset",
            "email": "test@test.ua",
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

        assert (
            e.value.error
            == f"Field: `replace_from` sibling field is not exists: {target_field}"
        )

    def test_transmute_replace_from(self, tsm_schema):
        pass

    def test_transmute_deep_nested(self, tsm_schema):
        data: dict[str, Any] = {
            "title": "Test-dataset",
            "email": "test@test.ua",
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

        assert data == {
            "name": "test-dataset",
            "email": "test@test.ua",
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
        with pytest.raises(logic.ValidationError):
            call_action(
                "tsm_transmute",
                schema={"root": "Dataset", "types": {"Dataset": {}}},
            )

    def test_transmute_no_schema(self):
        """Schema is required"""
        with pytest.raises(logic.ValidationError):
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
