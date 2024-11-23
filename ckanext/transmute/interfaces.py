from __future__ import annotations

from typing import Any

from ckan.plugins.interfaces import Interface


class ITransmute(Interface):
    """Main extension point of ckanext-transmute."""

    def get_transmutators(self) -> dict[str, Any]:
        """Register custom transmutation functions.

        Example:
            ```python
            def get_transmutators(self):
                return {
                    "tsm_title_case": tsm_title_case,
                    "tsm_is_email": tsm_is_email
                }
            ```

        Returns:
            Mapping with transmutaion functions.
        """
        return {}


    def get_transmutation_schemas(self) -> dict[str, dict[str, Any]]:
        """Register definitions of named schemas.

        These schemas can be reffered by name in code. In this way you can
        define static schema and apply in multiple places it to arbitrary data.

        Example:
            ```python
            def get_transmutation_schemas(self):
                person = {
                    "fields": {
                        "age": {"validators": ["int_validator"]},
                        "name": {"default": "John Doe"},
                    }
                }

                schema = {
                    "root": "person",
                    "types": {"person": person}
                }

                return {"person": schema}
            ```

        Returns:
            Mapping with definitions of named schemas.
        """
        return {}
