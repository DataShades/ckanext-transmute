from __future__ import annotations

from typing import Any
from ckanext.transmute.exception import SchemaParsingError

import pytest

import ckan.lib.helpers as h
import ckan.logic as logic
from ckan.tests.helpers import call_action


@pytest.mark.ckan_config("ckan.plugins", "scheming_datasets")
class TestTransmuteAction:
    def test_transmute_default(self, tsm_schema):
        data: dict[str, Any] = {
            "title": "Test-dataset",
            "email": "test@test.ua",
            "metadata_created": "",
        }

        result = call_action(
            "tsm_transmute",
            data=data,
            schema=tsm_schema,
            root="Dataset",
        )

        assert result["metadata_created"] == h.date_str_to_datetime(
            "2022-02-03T15:54:26.359453"
        )

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
