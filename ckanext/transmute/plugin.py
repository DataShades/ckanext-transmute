from __future__ import annotations

import json
from typing import Any

import ckan.plugins as p
import ckan.plugins.toolkit as tk

from ckanext.transmute.interfaces import ITransmute
from ckanext.transmute.transmutators import get_transmutators

from . import utils


@tk.blanket.actions
@tk.blanket.auth_functions
class TransmutePlugin(p.SingletonPlugin):
    p.implements(p.IConfigurer)
    p.implements(ITransmute)

    # IConfigurer
    def update_config(self, config_):
        tk.add_template_directory(config_, "templates")
        tk.add_resource("assets", "transmute")
        utils.collect_schemas()

    # ITransmute
    def get_transmutators(self):
        return get_transmutators()

    def get_transmutation_schemas(self) -> dict[str, Any]:
        prefix = "ckanext.transmute.schema."
        schemas: dict[str, Any] = {}
        for key in tk.config:
            if not key.startswith(prefix):
                continue
            with open(tk.config[key]) as src:
                schemas[key[len(prefix) :]] = json.load(src)
        return schemas
