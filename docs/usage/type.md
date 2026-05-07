Type description contains definition of its fields and a number of additional
settings.

```json
{
    "root": "main",
    "types": {
        "main": {
            "fields": {
                "first": {},
                "second": {}
            }
        }
    }
}
```

Every field either refers a different type if it's defined with `multiple:
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

## Type-level settings

These settings are placed directly on the type object, not inside a field definition.

### `drop_unknown_fields`

When `true`, any field present in the data but **not listed** in the type's
`fields`, `pre-fields`, or `post-fields` is removed from the output. This turns
the type definition into a whitelist — only explicitly declared fields survive.

```json
{
    "root": "Dataset",
    "types": {
        "Dataset": {
            "drop_unknown_fields": true,
            "fields": {
                "title": {},
                "notes": {}
            }
        }
    }
}
```

Given input `{"title": "T", "notes": "N", "internal_id": 42}`, the result
will be `{"title": "T", "notes": "N"}` — `internal_id` is dropped.

### `pre-fields` and `post-fields`

Besides `fields`, a type can also declare `pre-fields` and `post-fields`. All
three groups use the same field definition syntax. The processing order is
always:

1. `pre-fields`
2. `fields`
3. `post-fields`

Within each group, fields are sorted by their `weight` attribute (ascending,
default `0`). This is useful when one field depends on another being fully
processed first — for example, a `replace_from` field needs its source to be
resolved before it runs.

```json
{
    "root": "Dataset",
    "types": {
        "Dataset": {
            "pre-fields": {
                "title": {"validators": ["tsm_to_lowercase"]}
            },
            "fields": {
                "name": {"replace_from": "title"}
            },
            "post-fields": {
                "name": {"validators": ["tsm_name_validator"]}
            }
        }
    }
}
```

## Field attributes

Here's the full list of attributes that can be used in a field definition:

| Attribute          | Description                                                                          |
|--------------------|--------------------------------------------------------------------------------------|
| `map`              | New name of the field in the output                                                  |
| `validators`       | List of transmutators applied to the field value                                     |
| `remove`           | When `true`, removes the field from the data entirely                                |
| `default`          | Fallback value used only when the field is missing or empty                          |
| `default_from`     | Name(s) of other field(s) used as source of default value                            |
| `value`            | Static value that unconditionally replaces any existing value                        |
| `replace_from`     | Name(s) of other field(s) whose value unconditionally replaces this field's value    |
| `inherit_mode`     | How multiple `replace_from`/`default_from` sources are merged (see below)            |
| `validate_missing` | When `true`, runs validators even if the field is absent from the data               |
| `weight`           | Integer controlling processing order within a field group (default: `0`)             |
| `update`           | When `true`, merges `value` into the existing field value instead of replacing it    |

### `inherit_mode`

Applies when `replace_from` or `default_from` is given a list of field names.
Controls how values from multiple source fields are combined:

- `combine` *(default)* — all source field values are combined into a single
  list. Scalar values are wrapped in a list; list values are flattened in.
- `first-filled` — the first non-empty source field value is used as-is.

```json
{
    "tags": {
        "replace_from": ["topic", "subject"],
        "inherit_mode": "combine"
    },
    "license": {
        "default_from": ["license_url", "license_title"],
        "inherit_mode": "first-filled"
    }
}
```

## Field value precedence

When multiple value-setting attributes are present on a field, they are applied
in this fixed order:

1. **`default_from`** — copies a value from another field, but only if the
   current field is empty.
2. **`replace_from`** — copies a value from another field unconditionally.
3. **`default`** — sets a fallback value, but only if the field is still empty
   after steps 1–2.
4. **`value`** — sets a static value unconditionally. This always wins,
   overriding anything set by the steps above.
5. **validators** — run on whatever value survived steps 1–4.

!!! warning
    `value` always wins. Setting both `value` and `replace_from` on the same
    field means `replace_from` is effectively ignored — the static `value` will
    always overwrite it. If you need a conditional fallback, use the `default`
    argument of `tsm_mapper` instead of the field-level `value`.
