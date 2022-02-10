from __future__ import annotations

from typing import Any

import ckan.plugins.toolkit as tk
from ckan.logic import validate

from ckanext.transmute.types import TransmuteData
from ckanext.transmute.schema import SchemaParser, transmute_schema


@tk.side_effect_free
@validate(transmute_schema)
def transmute(ctx: dict[str, Any], data_dict: TransmuteData) -> dict[str, Any]:
    """Transmutes data with the provided convertion scheme
    The function doesn't changes the original data, but creates
    a new data dict.

    Args:
        ctx: CKAN context dict
        data: A data dict to transmute
        schema: schema to transmute data

    Returns:
        Transmuted data dict
    """
    tk.check_access("tsm_get_schemas", ctx, data_dict)

    data = data_dict["data"]
    schema = SchemaParser(data_dict["schema"])
    # _mutate_data(data, schema, "Dataset")

    return data
