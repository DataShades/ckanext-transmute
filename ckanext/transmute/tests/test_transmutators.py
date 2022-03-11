from __future__ import annotations

from typing import Any

import pytest

import ckan.lib.helpers as h
from ckan.tests.helpers import call_action

from ckanext.transmute.tests.helpers import build_schema


@pytest.mark.ckan_config("ckan.plugins", "scheming_datasets")
class TestTransmutators:
    def test_allow_resources_transmutator(self):
        data: dict[str, Any] = {
            "resources": [
                {
                    "title": "res1",
                    "format": "xml",
                },
                {
                    "title": "res1",
                    "format": "csv",
                },
                {
                    "title": "res1",
                    "format": "pptx",
                },
            ],
        }

        tsm_schema = build_schema(
            {
                "resources": {
                    "validators": [
                        ["tsm_allow_res_formats", "format", ["xml", "csv"]]],
                },
            }
        )

        result = call_action(
            "tsm_transmute",
            data=data,
            schema=tsm_schema,
            root="Dataset",
        )

        assert len(result['resources']) == 2
