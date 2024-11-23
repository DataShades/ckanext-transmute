[![Tests](https://github.com/DataShades/ckanext-transmute/actions/workflows/test.yml/badge.svg)](https://github.com/DataShades/ckanext-transmute/actions/workflows/test.yml)

# ckanext-transmute

Pipeline for data validation and conversion using schemas.


Read the [documentation](https://datashades.github.io/ckanext-transmute/) for a
full user guide.

## Quickstart


Install the extension
```sh
pip install ckanext-transmute
```

Add `transmute` to the list of enabled plugins in the CKAN config file.

Transform data using inline schema
```sh
ckanapi action tsm_transmute root=example data:'{"greeting": "hello"}' schema:'{
  "root": "example",
  "types": {
    "example": {
      "fields": {
        "message": {
          "validate_missing": true,
          "validators": [
            [
              "tsm_concat",
              "$greeting",
              ", ",
              "$name",
              "!"
            ]
          ],
          "weight": 2
        },
        "name": {
          "default": "transmute"
        },
        "greeting": {
          "default": "Hi"
        }
      },
      "post-fields": {
        "greeting": {
          "remove": true
        },
        "name": {
          "remove": true
        }
      }
    }
  }
}'
```


## Developer installation

Install the extension

```sh
git clone https://github.com/DataShades/ckanext-transmute.git
cd ckanext-transmute
pip install -e '.[dev]'
```

Run tests

```sh
pytest
```

## License

[AGPL](https://www.gnu.org/licenses/agpl-3.0.en.html)
