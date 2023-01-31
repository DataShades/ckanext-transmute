from __future__ import annotations
import logging

import ckan.plugins as p

from ckanext.transmute.exception import UnknownTransmutator
from ckanext.transmute.interfaces import ITransmute
from ckanext.transmute.types import MODE_COMBINE, MODE_FIRST_FILLED

_transmutator_cache = {}
log = logging.getLogger(__name__)


def get_transmutator(transmutator: str):
    get_all_transmutators()

    try:
        return _transmutator_cache[transmutator]
    except KeyError:
        raise UnknownTransmutator(f"Transmutator {transmutator} does not exist")


def get_all_transmutators() -> list[str]:
    if not _transmutator_cache:
        for plugin in reversed(list(p.PluginImplementations(ITransmute))):
            for name, fn in plugin.get_transmutators().items():
                log.debug(
                    f"Transmutator function {name} from plugin {plugin.name} was inserted"
                )
                _transmutator_cache[name] = fn

    return list(_transmutator_cache.keys())


def get_json_schema():
    transmutators = get_all_transmutators()
    return {
        "$schema": "http://json-schema.org/draft-04/schema",
        "type": "object",
        "properties": {
            "tsm_schema": {
                "type": "object",
                "properties": {
                    "root": {
                        "type": "string",
                        "minLength": 1,
                        "pattern": "^[A-Za-z_-]*$",
                    },
                    "types": {
                        "type": "object",
                        "minProperties": 1,
                        "propertyNames": {"pattern": "^[A-Za-z_-]*$"},
                        "additionalProperties": {
                            "type": "object",
                            "required": ["fields"],
                            "properties": {
                                "fields": {
                                    "type": "object",
                                    "minProperties": 1,
                                    "propertyNames": {"pattern": "^[A-Za-z_-]*$"},
                                    "additionalProperties": {
                                        "type": "object",
                                        "additionalProperties": False,
                                        "properties": {
                                            "validators": {
                                                "type": "array",
                                                "minItems": 1,
                                                "items": {
                                                    "oneOf": [
                                                        {
                                                            "type": "string",
                                                            "enum": transmutators,
                                                        },
                                                        {
                                                            "type": "array",
                                                            "minItems": 2,
                                                            "items": [
                                                                {
                                                                    "type": "string",
                                                                    "enum": transmutators,
                                                                }
                                                            ],
                                                            "additionalItems": {
                                                                "$ref": "#/$defs/anytype"
                                                            },
                                                        },
                                                    ]
                                                },
                                            },
                                            "map": {"type": "string"},
                                            "default": {"$ref": "#/$defs/anytype"},
                                            "default_from": {
                                                "anyOf": [
                                                    {
                                                        "type": "array",
                                                        "minItems": 1,
                                                        "items": {"type": "string"},
                                                    },
                                                    {"type": "string"},
                                                ]
                                            },
                                            "replace_from": {
                                                "anyOf": [
                                                    {
                                                        "type": "array",
                                                        "minItems": 1,
                                                        "items": {"type": "string"},
                                                    },
                                                    {"type": "string"},
                                                ]
                                            },
                                            "inherit_mode": {
                                                "type": "string",
                                                "items": {
                                                    "oneOf": [
                                                        {
                                                            "type": "string",
                                                            "enum": [MODE_COMBINE, MODE_FIRST_FILLED],
                                                        }
                                                    ]
                                                },
                                            },
                                            "value": {"$ref": "#/$defs/anytype"},
                                            "multiple": {"type": "boolean"},
                                            "remove": {"type": "boolean"},
                                            "type": {"type": "string"},
                                            "update": {"type": "boolean"},
                                        },
                                    },
                                }
                            },
                        },
                    },
                },
                "required": ["root", "types"],
            }
        },
        "$defs": {
            "anytype": {
                "type": ["number", "string", "boolean", "object", "array", "null"]
            }
        },
    }
