# ckanext-transmute
The extension helps to validate and converts a dataset based on a specific schema.

## Working with transmute

`ckanext-transmute` provides an action `tsm_transmute` It helps us to transmute data with the provided convertion scheme. The action doesn't change the original data, but creates a new data dict. There are two mandatory arguments - `data` and `schema`. `data` is a data dict you have and `schema` helps you to validate/change data in it.

Example:
We have a data dict:
```
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
```
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

There are few default transmutators you can use in your schema. Of course, you can define a custom transmutator with the CKAN `IValidators` interface.
- `tsm_name_validator` - Wrapper over CKAN default `name_validator` validator
- `tsm_to_lowercase` - Casts string value to a lowercase
- `tsm_to_uppercase` - Casts string value to a uppercase
- `tsm_string_only` - Validates if `field.value` is string
- `tsm_isodate` - Wrapper over CKAN default `isodate` validator. Mutates an iso-like string to datetime object
- `tsm_to_string` - Casts a `field.value` to `str`
- `tsm_get_nested` - Allows you to pick up a value from a nested structure. Example:
```         
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

The default transmutator must receive at least one mandatory argument - `field` object. Field contains few properties: `field_name`, `value` and `type`.

There is a possibility to provide more arguments to a validator like in `tsm_get_nested`. For this use a nested array with first item transmutator and other - arguments to it.


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
