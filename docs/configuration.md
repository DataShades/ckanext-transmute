## Named schemas

### `ckanext.transmute.schema.<NAME>`

Path to a JSON file containing a transmutation schema. The `<NAME>` part
becomes the schema's identifier and can be passed as the `schema` argument to
`tsm_transmute` instead of an inline dict.

**ckan.ini**

```ini
ckanext.transmute.schema.my_schema = /etc/ckan/schemas/my_schema.json
```

**Usage**

```python
import ckan.plugins.toolkit as tk

result = tk.get_action("tsm_transmute")(
    {},
    {"data": harvest_dict, "schema": "my_schema"},
)
```

Schemas are loaded once at startup. Changing the file on disk requires
restarting the CKAN process.

Named schemas can also be registered in code via the
[`ITransmute`](interfaces.md) interface, which is the preferred approach when
the schema is bundled with a plugin rather than deployed as a standalone file.

A path to the schema can be specified relative to the CKAN config directory.
Therefore, you can link the schema file from the plugin directory to the
config directory.
