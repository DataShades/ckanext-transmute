[![Tests](https://github.com/mutantsan/ckanext-transmute/actions/workflows/test.yml/badge.svg)](https://github.com/mutantsan/ckanext-transmute/actions/workflows/test.yml)

# ckanext-transmute
This extension helps to validate and convert data based on a specific schema.

## Working with transmute

`ckanext-transmute` provides an action `tsm_transmute`. It helps us to transmute data with the provided conversion scheme. The action doesn't change the original data but creates a new data dict. There are two mandatory arguments: `data` and `schema`. `data` is a data dict you have, and `schema` helps you to validate/change data in it.

### Example

We have a data dict:

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
                            "extra": "should-be-removed",
                        }
                    ],
                },
                {
                    "title": "test-res2",
                    "extension": "csv",
                    "web": "https://stackoverflow.com/",
                },
            ],
        }
```

And we want to achieve this:

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
                    "sub-resources": [{"name": "SUB-RES", "format": "CSV"}],
                },
                {
                    "name": "test-res2",
                    "format": "CSV",
                    "url": "https://stackoverflow.com/",
                },
            ],
        }
```

Then, our schema must be something like that:

```
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

There is an example of schema with nested types. The `root` field is mandatory, it's must contain a main type name, from which the scheme starts. As you can see, `Dataset` type contains `Resource` type which contans `Sub-Resource`.

### Transmutators

There are a few default transmutators you can use in your schema. Of course, you can define a custom transmutator with the `ITransmute ` interface.

- `tsm_name_validator` - Wrapper over CKAN default `name_validator` validator.
- `tsm_to_lowercase` - Casts string value to lowercase.
- `tsm_to_uppercase` - Casts string value to uppercase.
- `tsm_string_only` - Validates if `field.value` is a string.
- `tsm_isodate` - Validates datetime string. Mutates an iso-like string to datetime object.
- `tsm_to_string` - Casts a `field.value` to `str`.
- `tsm_get_nested` - Allows you to pick up a value from a nested structure. Example:
```py
data = "title_translated": [
    {"nested_field": {"en": "en title", "ar": "العنوان ar"}},
]

schema = ...
    "title": {
        "replace_from": "title_translated",
        "validators": [
            ["tsm_get_nested", 0, "nested_field", "en"],
            "tsm_to_uppercase",
        ],
    },
    ...
```
This will take a value for a `title` field from `title_translated` field. Because `title_translated` is an array with nested objects, we are using the `tsm_get_nested` transmutator to achieve the value from it.

- `tsm_trim_string` - Trim string with max length. Example to trim `hello world` to `hello`:
```py
data = {"field_name": "hello world}

schema = ...
    "field_name": {
        "validators": [
            ["tsm_trim_string", 5]
        ],
    },
    ...
```
- `tsm_concat` - Concatenate strings. Use `$self` to point on field value. Example:
```py
data = {"id": "dataset-1"}

schema = ...
    "package_url": {
        "replace_from": "id",
        "validators": [
            [
                "tsm_concat",
                "https://site.url/dataset/",
                "$self",
            ]
        ],
    },
    ...
```
- `tsm_unique_only` - Preserve only unique values from a list. Works only with lists.


The default transmutator must receive at least one mandatory argument - `field` object. Field contains few properties: `field_name`, `value` and `type`.

There is a possibility to provide more arguments to a validator like in `tsm_get_nested`. For this use a nested array with first item transmutator and other - arguments to it.

- `tsm_mapper` - Map current value to the mapping dict

Map a value to another value. The current value must serve as a key within the mapping dictionary, while the new value will represent the updated value.

The default value to be used when the key is not found in the mapping. If the default value is not provided, the current value will be used as it.

```py
data = {"language": "English"}

schema = ...
    "language": {
        "validators": [
            [
                "tsm_mapper",
                {"English": "eng"},
                "English"
            ]
        ]
    },
    ...
```

- `tsm_list_mapper` - Map current value to the mapping dict

Works as `tsm_mapper` but with list. Doesn't have a `default` value. Third argument `remove` must be `True` or `False`.

If `remove` set to True, removes values from the list if they don't have a corresponding mapping. Defaults to `False`.

Example without `remove`:

```py
data = {"topic": ["Health", "Military", "Utilities"]}

schema = ...
    "topic": {
        "validators": [
            [
                "tsm_list_mapper",
                {"Military": "Army", "Utilities": "Utility"}
            ]
        ]
    },
    ...
```

The result here will be `["Health", "Army", "Utility"]`
And here's an example with remove:

```py
data = {"topic": ["Health", "Military", "Utilities"]}

schema = build_schema(
    "topic": {
        "validators": [
            [
                "tsm_list_mapper",
                {"Military": "Army", "Utilities": "Utility"},
                True
            ]
        ]
    },
    ...
)
```
This will result in `["Army", "Utility"]`, and the `Health` will be deleted, cause it doesn't have a mapping.

### Keywords
1. `map` (`str`) - changes the `field.name` in result dict.
2. `validators` (`list[str]`) - a list of transmutators that will be applied to a `field.value`. A transmutator could be a `string` or a `list` where the first item must be transmutator name and others are arbitrary values. Example:
    ```
    ...
    "validators": [
        ["tsm_get_nested", "nested_field", "en"],
        "tsm_to_uppercase",
    ,
    ...
    ```
    There are two transmutators: `tsm_get_nested` and `tsm_to_uppercase`.
3. `multiple` (`bool`, default: `False`) - if the field could have multiple items, e.g `resources` field in dataset, mark it as `multiple` to transmute all the items successively.
    ```
    ...
    "resources": {
        "type": "Resource",
        "multiple": True
    },
    ...
    ```
4. `remove` (`bool`, default: `False`) - Removes a field from a result dict if `True`.
5. `default` (`Any`) - the default value that will be used if the original field.value evaluates to `False`.
6. `default_from` (`str` | `list`) - acts similar to `default` but accepts a `field.name` of a sibling field from which we want to take its value. Sibling field is a field that located in the same `type`. The current implementation doesn't allow to point on fields from other `types`. Could take a string that represents the `field.name` or an array of strings, to use multiple fields. See `inherit_mode` keyword for details.
    ```
    ...
    "metadata_modified": {
        "validators": ["tsm_isodate"],
        "default_from": "metadata_created",
    },
    ...
    ```
7. `replace_from` (`str`| `list`) - acts similar to `default_from` but replaces the origin value whenever it's empty or not.
8. `inherit_mode` (`str`, default: `combine`) - defines the mode for `default_from` and `replace_from`. By default we are combining values
from all the fields, but we could just use first non-false value, in case if the field might be empty.
9. `value` (`Any`) - a value that will be used for a field. This keyword has the highest priority. Could be used to create a new field with an arbitrary value.
10. `update` (`bool`, default: `False`) - if the original value is mutable (`array`, `object`) - you can update it. You can only update field values of the same types.

## Installation

To install ckanext-transmute:

1. Activate your CKAN virtual environment, for example:

     . /usr/lib/ckan/default/bin/activate

2. Clone the source and install it on the virtualenv

    git clone https://github.com/mutantsan/ckanext-transmute.git
    cd ckanext-transmute
    pip install -e .
	pip install -r requirements.txt

3. Add `transmute` to the `ckan.plugins` setting in your CKAN
   config file (by default the config file is located at
   `/etc/ckan/default/ckan.ini`).

4. Restart CKAN. For example if you've deployed CKAN with Apache on Ubuntu:

     sudo service apache2 reload


## Developer installation

To install ckanext-transmute for development, activate your CKAN virtualenv and
do:

    git clone https://github.com/mutantsan/ckanext-transmute.git
    cd ckanext-transmute
    python setup.py develop
    pip install -r dev-requirements.txt


## Tests

I've used TDD to write this extension, so if you changing something be sure that all the tests are valid. To run the tests, do:

    pytest --ckan-ini=test.ini

## License

[AGPL](https://www.gnu.org/licenses/agpl-3.0.en.html)
