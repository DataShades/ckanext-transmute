from __future__ import annotations

import json
from typing import Any

import ckan.plugins as p
import ckan.plugins.toolkit as tk

from ckanext.transmute.interfaces import ITransmute
from ckanext.transmute.logic.action import get_actions
from ckanext.transmute.logic.auth import get_auth_functions
from ckanext.transmute.transmutators import get_transmutators

from . import utils


class TransmutePlugin(p.SingletonPlugin):
    p.implements(p.IConfigurer)
    p.implements(p.IActions)
    p.implements(p.IAuthFunctions)
    p.implements(ITransmute)

    # IConfigurer
    def update_config(self, config_):
        tk.add_template_directory(config_, "templates")
        tk.add_resource("assets", "transmute")
        utils.collect_schemas()

    # IActions
    def get_actions(self):
        """Registers a list of extension specific actions."""
        return get_actions()

    # IAuthFunctions
    def get_auth_functions(self):
        """Registers a list of extension specific auth function."""
        return get_auth_functions()

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
