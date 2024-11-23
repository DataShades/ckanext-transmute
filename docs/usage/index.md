# Overview

`ckanext-transmute` registers an action `tsm_transmute` to transmute data using
the provided conversion scheme. The action doesn't change the original data but
creates a new data dict. There are two mandatory arguments: `data` and
`schema`. `data` is a data dict you need to transform, and `schema` contains
the rules describing all the transformation steps.

Typical use-case for it is transforming existing data, like this:

```json
{
  "title": "Test-dataset",
  "email": "test@test.ua",
  "metadata_created": "",
  "metadata_modified": "",
  "metadata_reviewed": "",
  "resources": [
    {
      "title": "test-res",
      "extension": "xml",
      "web": "https://stackoverflow.com/",
      "sub-resources": [
        {
          "title": "sub-res",
          "extension": "csv",
          "extra": "should-be-removed"
        }
      ]
    },
    {
      "title": "test-res2",
      "extension": "csv",
      "web": "https://stackoverflow.com/"
    }
  ]
}

```

into expected data, like this:

```py
{
    "name": "test-dataset",
    "email": "test@test.ua",
    "metadata_created": datetime.datetime(2022, 2, 3, 15, 54, 26, 359453),
    "metadata_modified": datetime.datetime(2022, 2, 3, 15, 54, 26, 359453),
    "metadata_reviewed": datetime.datetime(2022, 2, 3, 15, 54, 26, 359453),
    "attachments": [
        {
            "name": "test-res",
            "format": "XML",
            "url": "https://stackoverflow.com/",
            "sub-resources": [{"name": "SUB-RES", "format": "CSV"}]
        },
        {
            "name": "test-res2",
            "format": "CSV",
            "url": "https://stackoverflow.com/"
        }
    ]
}
```

To achieve this goal, the following schema definition can be used:
```python
{
    "root": "Dataset",
    "types": {
        "Dataset": {
            "fields": {
                "title": {
                    "validators": [
                        "tsm_string_only",
                        "tsm_to_lowercase",
                        "tsm_name_validator",
                    ],
                    "map": "name",
                },
                "resources": {
                    "type": "Resource",
                    "multiple": True,
                    "map": "attachments",
                },
                "metadata_created": {
                    "validators": ["tsm_isodate"],
                    "default": "2022-02-03T15:54:26.359453",
                },
                "metadata_modified": {
                    "validators": ["tsm_isodate"],
                    "default_from": "metadata_created",
                },
                "metadata_reviewed": {
                    "validators": ["tsm_isodate"],
                    "replace_from": "metadata_modified",
                },
            }
        },
        "Resource": {
            "fields": {
                "title": {
                    "validators": ["tsm_string_only"],
                    "map": "name",
                },
                "extension": {
                    "validators": ["tsm_string_only", "tsm_to_uppercase"],
                    "map": "format",
                },
                "web": {
                    "validators": ["tsm_string_only"],
                    "map": "url",
                },
                "sub-resources": {
                    "type": "Sub-Resource",
                    "multiple": True,
                },
            },
        },
        "Sub-Resource": {
            "fields": {
                "title": {
                    "validators": ["tsm_string_only", "tsm_to_uppercase"],
                    "map": "name",
                },
                "extension": {
                    "validators": ["tsm_string_only", "tsm_to_uppercase"],
                    "map": "format",
                },
                "extra": {
                    "remove": True,
                },
            }
        },
    },
}
```

This is an example of schema with nested types. The `root` field defines the
type of the outer layer of data, while `sub-resources` field inside the
definition of the root type contain `type` references to `Sub-Resource`
definition.
