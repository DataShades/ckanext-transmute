from __future__ import annotations
from re import T

from typing import Any

import pytest

from ckan.tests.helpers import call_action
from ckan.logic import ValidationError

from ckanext.transmute.tests.helpers import build_schema
from ckanext.transmute.exception import TransmutatorError


@pytest.mark.ckan_config("ckan.plugins", "scheming_datasets")
class TestTransmutators:
    def test_transmute_validator_without_args(self):
        data = {
            "field1": [
                {"nested_field": {"foo": 2, "bar": 2}},
            ]
        }

        tsm_schema = build_schema({"field1": {"validators": [["tsm_get_nested"]]}})

        with pytest.raises(TransmutatorError) as e:
            call_action(
                "tsm_transmute",
                data=data,
                schema=tsm_schema,
                root="Dataset",
            )

        assert e.value.error == "Arguments for validator weren't provided"

    def test_trim_string_transmutator(self):
        data: dict[str, Any] = {
            "field_name": "hello world",
        }

        tsm_schema = build_schema(
            {"field_name": {"validators": [["tsm_trim_string", 5]]}}
        )

        result = call_action(
            "tsm_transmute",
            data=data,
            schema=tsm_schema,
            root="Dataset",
        )

        assert result["field_name"] == "hello"

    def test_trim_string_transmutator_with_zero_max_length(self):
        data: dict[str, Any] = {
            "field_name": "hello world",
        }

        tsm_schema = build_schema(
            {"field_name": {"validators": [["tsm_trim_string", 0]]}}
        )

        result = call_action(
            "tsm_transmute",
            data=data,
            schema=tsm_schema,
            root="Dataset",
        )

        assert result["field_name"] == ""

    def test_trim_string_transmutator_with_two_args(self):
        data: dict[str, Any] = {
            "field_name": "hello world",
        }

        tsm_schema = build_schema(
            {"field_name": {"validators": [["tsm_trim_string", 0, 1]]}}
        )

        with pytest.raises(TransmutatorError) as e:
            result = call_action(
                "tsm_transmute",
                data=data,
                schema=tsm_schema,
                root="Dataset",
            )

    def test_trim_string_transmutator_with_not_integer_length(self):
        data: dict[str, Any] = {
            "field_name": "hello world",
        }

        tsm_schema = build_schema(
            {"field_name": {"validators": [["tsm_trim_string", "0"]]}}
        )

        with pytest.raises(ValidationError) as e:
            result = call_action(
                "tsm_transmute",
                data=data,
                schema=tsm_schema,
                root="Dataset",
            )

        assert "max_length must be integer" in str(e)

    def test_concat_transmutator_with_self(self):
        data: dict[str, Any] = {
            "identifier": "right-to-the-night-results",
        }

        tsm_schema = build_schema(
            {
                "field_name": {
                    "replace_from": "identifier",
                    "validators": [
                        [
                            "tsm_concat",
                            "https://ckan.url/dataset/",
                            "$self",
                            "/information",
                        ]
                    ],
                },
                "identifier": {},
            }
        )

        result = call_action(
            "tsm_transmute",
            data=data,
            schema=tsm_schema,
            root="Dataset",
        )

        new_field_value = f"https://ckan.url/dataset/{data['identifier']}/information"
        assert result["field_name"] == new_field_value

    def test_concat_transmutator_without_self(self):
        """You can skip using $self if you want for some reason"""
        data: dict[str, Any] = {
            "identifier": "right-to-the-night-results",
        }

        tsm_schema = build_schema(
            {
                "field_name": {
                    "replace_from": "identifier",
                    "validators": [
                        [
                            "tsm_concat",
                            "https://ckan.url/dataset/",
                            "information",
                        ]
                    ],
                },
                "identifier": {},
            }
        )

        result = call_action(
            "tsm_transmute",
            data=data,
            schema=tsm_schema,
            root="Dataset",
        )

        new_field_value = f"https://ckan.url/dataset/information"
        assert result["field_name"] == new_field_value

    def test_concat_transmutator_with_not_string_arg(self):
        """You can skip using $self if you want for some reason"""
        data: dict[str, Any] = {
            "identifier": "right-to-the-night-results",
        }

        tsm_schema = build_schema(
            {
                "field_name": {
                    "replace_from": "identifier",
                    "validators": [
                        [
                            "tsm_concat",
                            "https://ckan.url/dataset/",
                            1,
                        ]
                    ],
                },
                "identifier": {},
            }
        )

        result = call_action(
            "tsm_transmute",
            data=data,
            schema=tsm_schema,
            root="Dataset",
        )

        new_field_value = f"https://ckan.url/dataset/1"
        assert result["field_name"] == new_field_value

    def test_concat_transmutator_with_field_link(self):
        """We are able to use fields from schema as a concat item"""

        data: dict[str, Any] = {
            "identifier": "right-to-the-night-results",
            "url": "https://ckan.url/dataset/",
        }

        tsm_schema = build_schema(
            {
                "url": {
                    "validators": [
                        [
                            "tsm_concat",
                            "https://ckan.url/dataset/",
                            "$identifier",
                        ]
                    ],
                },
                "identifier": {},
            }
        )

        result = call_action(
            "tsm_transmute",
            data=data,
            schema=tsm_schema,
            root="Dataset",
        )

        new_field_value = "https://ckan.url/dataset/right-to-the-night-results"
        assert result["url"] == new_field_value

    def test_concat_transmutator_with_field_link_nested(self):
        """We are able to use fields from schema as a concat
        item from within nested structure"""

        data: dict[str, Any] = {
            "title": "Package title",
            "resources": [
                {"title": "test res 1", "format": "xml"},
                {"title": "test res 2", "format": "csv"},
            ],
        }

        tsm_schema = {
            "root": "Dataset",
            "types": {
                "Dataset": {
                    "fields": {
                        "title": {},
                        "resources": {
                            "type": "Resource",
                            "multiple": True,
                        },
                    }
                },
                "Resource": {
                    "fields": {
                        "format": {
                            "validators": ["tsm_string_only", "tsm_to_uppercase"],
                        },
                        "title": {
                            "replace_from": "format",
                            "validators": [
                                "tsm_to_uppercase",
                                [
                                    "tsm_concat",
                                    "$title",
                                    " ",
                                    "$self",
                                ],
                            ],
                        },
                    },
                },
            },
        }

        result = call_action(
            "tsm_transmute",
            data=data,
            schema=tsm_schema,
            root="Dataset",
        )

        for res in result["resources"]:
            assert (
                res["title"] == f"{result['title']} {res['format'].upper()}"
            )

    def test_unique_only(self):
        """You can skip using $self if you want for some reason"""
        data: dict[str, Any] = {"field_name": [1, 2, 3, 3, 4, 5, 6, 6]}

        tsm_schema = build_schema(
            {
                "field_name": {
                    "validators": ["tsm_unique_only"],
                },
            }
        )

        result = call_action(
            "tsm_transmute",
            data=data,
            schema=tsm_schema,
            root="Dataset",
        )

        assert result["field_name"] == [1, 2, 3, 4, 5, 6]

    def test_unique_only_for_not_list(self):
        """You can skip using $self if you want for some reason"""
        data: dict[str, Any] = {"field_name": 1}

        tsm_schema = build_schema(
            {
                "field_name": {
                    "validators": ["tsm_unique_only"],
                },
            }
        )
        with pytest.raises(ValidationError) as e:
            call_action(
                "tsm_transmute",
                data=data,
                schema=tsm_schema,
                root="Dataset",
            )

    def test_unique_only_empty_list(self):
        """You can skip using $self if you want for some reason"""
        data: dict[str, Any] = {"field_name": []}

        tsm_schema = build_schema(
            {
                "field_name": {
                    "validators": ["tsm_unique_only"],
                },
            }
        )

        result = call_action(
            "tsm_transmute",
            data=data,
            schema=tsm_schema,
            root="Dataset",
        )

        assert result["field_name"] == []
