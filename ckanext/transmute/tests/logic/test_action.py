from __future__ import annotations

import json
from typing import Any

import pytest

import ckan.lib.helpers as h
import ckan.plugins.toolkit as tk
from ckan.logic import ValidationError
from ckan.tests.helpers import call_action

from ckanext.transmute import utils as transmute_utils
from ckanext.transmute.exception import SchemaParsingError
from ckanext.transmute.tests.helpers import build_schema
from ckanext.transmute.types import MODE_FIRST_FILLED


@pytest.mark.usefixtures("with_plugins")
class TestTransmuteAction:
    def test_custom_root(self):
        """Action allows using a root different from "Dataset"."""
        result = call_action(
            "tsm_transmute",
            data={},
            schema={
                "root": "custom",
                "types": {"custom": {"fields": {"def": {"default": "test"}}}},
            },
            root="custom",
        )
        assert result == {"def": "test"}

    def test_transmute_default(self):
        """If the origin evaluates to False it must be replaced
        with the default value.
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

        assert result["metadata_created"] == h.date_str_to_datetime(metadata_created_default)

    def test_transmute_default_with_origin_value(self):
        """The default value mustn't replace the origin value."""
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
        value is empty.
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
        """The target field value could be empty."""
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

    def test_transmute_replace_from(self):
        """The `replace_from` must copy value from target field and replace
        the origin value whether it is empty or not.
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
        """Replace from multiple fields must combine values of those fields."""
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

    def test_transmute_replace_from_multiple_different_types(self):
        """Replace from multiple fields must combine values of those fields."""
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

        assert result["field_4"] == data["field_1"] + [data["field_2"]] + [data["field_3"]]

    def test_transmute_default_from_multiple(self):
        """Default from multiple fields must combine values of those fields."""
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

    def test_transmute_default_from_multiple_different_types(self):
        """Default from multiple fields must combine values of those fields."""
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

        assert result["field_4"] == data["field_1"] + [data["field_2"]] + [data["field_3"]]

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
        """Field with `remove` must be excluded from the result."""
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
        it's empty or not.
        """
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
        assert result == {
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
        assert data["title"] == "Test-dataset"

    def test_transmute_no_field_schema(self):
        """If no fields specified, there is nothing to do."""
        result = call_action(
            "tsm_transmute",
            data={"title": "test"},
            schema={"root": "Dataset", "types": {"Dataset": {}}},
        )

        assert result == {"title": "test"}

    def test_transmute_no_data(self):
        """Data is required."""
        with pytest.raises(ValidationError):
            call_action(
                "tsm_transmute",
                schema={"root": "Dataset", "types": {"Dataset": {}}},
            )

    def test_transmute_no_schema(self):
        """Schema is required."""
        with pytest.raises(ValidationError):
            call_action("tsm_transmute", data={"title": "test"})

    def test_transmute_empty_data(self):
        """If there is no data, there is no sense to do anything."""
        result = call_action(
            "tsm_transmute",
            data={},
            schema={"root": "Dataset", "types": {"Dataset": {}}},
        )

        assert len(result) == 0

    def test_transmute_empty_schema(self):
        """Schema root type is required."""
        with pytest.raises(SchemaParsingError) as e:
            call_action("tsm_transmute", data={"title": "test"}, schema={})

        assert e.value.error == "Schema: root type is missing"

    def test_transmute_new_field_inherit(self):
        """We can define a new field in schema and it will be
        added to the result data.
        """
        data: dict[str, Any] = {
            "metadata_created": "hello world",
        }

        tsm_schema = build_schema(
            {
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

        assert result["metadata_modified"] == result["metadata_created"]

    def test_transmute_new_field_from_default_and_value(self):
        """Default runs after value."""
        data: dict[str, Any] = {}

        tsm_schema = build_schema({"field1": {"default": 101, "value": 102}})

        result = call_action(
            "tsm_transmute",
            data=data,
            schema=tsm_schema,
            root="Dataset",
        )

        assert "field1" in result
        assert result["field1"] == 102

    def test_transmute_new_field_from_value(self):
        """We can define a new field in schema and it will be
        added to the result data.
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

        for _i in range(10):
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

        assert e.value.error_dict["resource_number"] == ["Field value is not mutable"]

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

        assert e.value.error_dict["extras"] == ["Original value has different type"]

    def test_transmute_replace_from_inherit_first_filled_first_true(self):
        """Replace from multiple fields must combine values of those fields."""
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
        """Replace from multiple fields must combine values of those fields."""
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
        """Replace from multiple fields must combine values of those fields."""
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


@pytest.mark.usefixtures("with_plugins")
class TestPrePostFields:
    def test_pre_fields_are_processed(self):
        """Fields in the pre-fields section run through validators like regular fields."""
        data: dict[str, Any] = {"title": "hello"}

        schema = {
            "root": "Dataset",
            "types": {
                "Dataset": {
                    "pre-fields": {"title": {"validators": ["tsm_to_uppercase"]}},
                    "fields": {},
                }
            },
        }

        result = call_action("tsm_transmute", data=data, schema=schema, root="Dataset")

        assert result["title"] == "HELLO"

    def test_post_fields_are_processed(self):
        """Fields in the post-fields section run through validators like regular fields."""
        data: dict[str, Any] = {"title": "hello"}

        schema = {
            "root": "Dataset",
            "types": {
                "Dataset": {
                    "fields": {},
                    "post-fields": {"title": {"validators": ["tsm_to_uppercase"]}},
                }
            },
        }

        result = call_action("tsm_transmute", data=data, schema=schema, root="Dataset")

        assert result["title"] == "HELLO"

    def test_pre_fields_run_before_fields(self):
        """A pre-field transformation is visible to regular fields processed afterward."""
        data: dict[str, Any] = {"source": "hello", "dest": ""}

        schema = {
            "root": "Dataset",
            "types": {
                "Dataset": {
                    "pre-fields": {"source": {"validators": ["tsm_to_uppercase"]}},
                    "fields": {
                        "source": {},
                        "dest": {"replace_from": "source"},
                    },
                }
            },
        }

        result = call_action("tsm_transmute", data=data, schema=schema, root="Dataset")

        # pre-fields uppercased "source" before fields copied it into "dest"
        assert result["source"] == "HELLO"
        assert result["dest"] == "HELLO"

    def test_post_fields_run_after_fields(self):
        """A post-field sees the value that regular fields already transformed."""
        data: dict[str, Any] = {"name": "hello", "summary": ""}

        schema = {
            "root": "Dataset",
            "types": {
                "Dataset": {
                    "fields": {
                        "name": {"validators": ["tsm_to_uppercase"]},
                        "summary": {},
                    },
                    "post-fields": {"summary": {"replace_from": "name"}},
                }
            },
        }

        result = call_action("tsm_transmute", data=data, schema=schema, root="Dataset")

        # post-fields copies "name" after fields already uppercased it
        assert result["name"] == "HELLO"
        assert result["summary"] == "HELLO"


@pytest.mark.usefixtures("with_plugins")
class TestValidateMissing:
    def test_absent_field_skipped_by_default(self):
        """A schema field not present in data is silently ignored without validate_missing."""
        result = call_action(
            "tsm_transmute",
            data={},
            schema=build_schema({"absent": {}}),
            root="Dataset",
        )

        assert "absent" not in result

    def test_validate_missing_adds_field_as_none(self):
        """validate_missing=True processes the absent field, producing None when no validators."""
        result = call_action(
            "tsm_transmute",
            data={},
            schema=build_schema({"missing": {"validate_missing": True}}),
            root="Dataset",
        )

        assert "missing" in result
        assert result["missing"] is None

    def test_validate_missing_runs_validators_on_absent_field(self):
        """validate_missing=True causes validators to execute even when the field is missing."""
        with pytest.raises(ValidationError):
            call_action(
                "tsm_transmute",
                data={},
                schema=build_schema(
                    {
                        "absent": {
                            "validate_missing": True,
                            "validators": ["tsm_string_only"],
                        }
                    }
                ),
                root="Dataset",
            )


@pytest.mark.usefixtures("with_plugins")
class TestWeightOrdering:
    def test_lower_weight_field_processed_first(self):
        """A field with weight=0 is processed before a field with weight=1."""
        data: dict[str, Any] = {"source": "hello", "dest": ""}

        schema = {
            "root": "Dataset",
            "types": {
                "Dataset": {
                    "fields": {
                        # source (weight 0) is uppercased first
                        "source": {"validators": ["tsm_to_uppercase"], "weight": 0},
                        # dest (weight 1) copies source after it was uppercased
                        "dest": {"replace_from": "source", "weight": 1},
                    }
                }
            },
        }

        result = call_action("tsm_transmute", data=data, schema=schema, root="Dataset")

        assert result["source"] == "HELLO"
        assert result["dest"] == "HELLO"

    def test_higher_weight_field_processed_later(self):
        """A field with weight=1 is processed after weight=0, so weight=0 misses the transform."""
        data: dict[str, Any] = {"source": "hello", "dest": ""}

        schema = {
            "root": "Dataset",
            "types": {
                "Dataset": {
                    "fields": {
                        # dest (weight 0) copies source before source is uppercased
                        "dest": {"replace_from": "source", "weight": 0},
                        # source (weight 1) is uppercased afterward
                        "source": {"validators": ["tsm_to_uppercase"], "weight": 1},
                    }
                }
            },
        }

        result = call_action("tsm_transmute", data=data, schema=schema, root="Dataset")

        assert result["source"] == "HELLO"
        # dest ran before source was transformed — it saw the original "hello"
        assert result["dest"] == "hello"


@pytest.mark.usefixtures("with_plugins")
class TestDropUnknownFields:
    def test_extra_fields_dropped_when_flag_set(self):
        """Fields present in data but absent from the schema are removed."""
        data: dict[str, Any] = {"known": "keep", "extra": "drop"}

        schema = {
            "root": "Dataset",
            "types": {
                "Dataset": {
                    "drop_unknown_fields": True,
                    "fields": {"known": {}},
                }
            },
        }

        result = call_action("tsm_transmute", data=data, schema=schema, root="Dataset")

        assert result == {"known": "keep"}
        assert "extra" not in result

    def test_extra_fields_kept_without_flag(self):
        """Without drop_unknown_fields, extra data fields pass through unchanged."""
        data: dict[str, Any] = {"known": "keep", "extra": "also kept"}

        result = call_action(
            "tsm_transmute",
            data=data,
            schema=build_schema({"known": {}}),
            root="Dataset",
        )

        assert result["extra"] == "also kept"

    def test_mapped_field_name_is_kept(self):
        """After a field is mapped to a new name, the new name is what's kept."""
        data: dict[str, Any] = {"original": "value", "extra": "drop"}

        schema = {
            "root": "Dataset",
            "types": {
                "Dataset": {
                    "drop_unknown_fields": True,
                    "fields": {"original": {"map": "renamed"}},
                }
            },
        }

        result = call_action("tsm_transmute", data=data, schema=schema, root="Dataset")

        assert "renamed" in result
        assert "original" not in result
        assert "extra" not in result


@pytest.mark.usefixtures("with_plugins")
class TestNamedSchema:
    def test_string_schema_name_resolves_from_cache(self, monkeypatch):
        """Passing a string as the schema argument resolves the named schema from cache."""

        monkeypatch.setitem(
            transmute_utils._schema_cache,
            "_test_named_schema",
            build_schema({"title": {"validators": ["tsm_to_uppercase"]}}),
        )

        result = call_action(
            "tsm_transmute",
            data={"title": "hello"},
            schema="_test_named_schema",
            root="Dataset",
        )

        assert result["title"] == "HELLO"

    def test_plugin_reads_schema_from_json_file(self, monkeypatch, tmp_path):
        """TransmutePlugin.get_transmutation_schemas reads JSON files pointed to by config."""

        schema_body = build_schema({"name": {"validators": ["tsm_to_lowercase"]}})
        schema_file = tmp_path / "schema.json"
        schema_file.write_text(json.dumps(schema_body))

        monkeypatch.setattr(tk, "config", {"ckanext.transmute.schema.loaded_schema": str(schema_file)})

        schemas = transmute_utils.collect_schemas()

        assert "loaded_schema" in schemas
        assert schemas["loaded_schema"] == schema_body
