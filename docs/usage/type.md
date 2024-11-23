Type description contains definition of its fields and a number of additional
settings.


```json
{
    "root": "main",
    "types": {
        "main": {
            "drop_unknown_fields": true,
            "fields": {
                "first": {},
                "second": {}
            }
        }
    }
}
```

Every field either refers a different type if it's definded with `multiple:
true` and `type: TYPE_NAME`, or contains inline definition. Inline fields are
used most often and their definition is flexible enough to cover majority of
use-cases.

```json
{
    "root": "main",
    "types": {
        "main": {
            "fields": {
                "inline_field": {"default": 42},
                "sub_type": {"multiple": true, "type": "secondary"}
            }
        },
        "secondary": {}
    }
}
```

Here's the list of attributes that can be used in the field definition:

| Attribute          | Description                                                           |
|--------------------|-----------------------------------------------------------------------|
| `map`              | New name of the field                                                 |
| `validators`       | List of transmutators applied to the field                            |
| `remove`           | Flag that removes field from data when enabled                        |
| `default`          | Default value if field is missing                                     |
| `default_from`     | Name of the field used as source of default value                     |
| `value`            | Static value that replaces any existing value of the field            |
| `replace_from`     | Name of the field used as a source of value                           |
| `validate_missing` | Flag that applies validation even if data does not contains the field |
| `weight`           | Weight that controls order of field processing                        |
