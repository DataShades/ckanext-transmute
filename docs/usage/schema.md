Transmutation schema represented by a dictionary that contains descriptions of
all data types used for transmutation and the name of the `root` type.

```json
{
    "root": "main",
    "types": {
        "main": {},
        "secondary": {}
    }
}
```

The `root` type is used for the initial transformation. If, during this
transformation, some of multi-values fields contain reference to other types
defined in schema, these types will be used for further transformation of data.

```json
{
    "root": "main",
    "types": {
        "main": {
            "drop_unknown_fields": true,
            "fields": {
                "child": {"type": "secondary", "multiple": true}
            }
        },
        "secondary": {
            "drop_unknown_fields": true,
            "fields": {"name": {}}
        }
    }
}
```

!!! note
    At the moment, only multivalued fields can be transformed using nested
    types. In future support for single-valued nested field will be added
