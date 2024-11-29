Transmutators are similar to CKAN validators. They accept the field and modify
it. But unlike validators, transmutators work with field and have access to the
whole schema definition.

Usually, transmutator is defined as a function with a single argument. This
argument always receives the instance of validated field. It's a dataclass with

* `field_name`: the name of processed field
* `value`: current value of the field
* `type`: the name of the type that contains field definition
* `data`: the whole data dictionary that is currently transmuted

To apply transmutator, add its name to the `validators` attribute of the field
definition in transmutation schema:

```json
{
    ...,
    "fields": {
        "my_field": {
            "validators": ["my_transmutator"]
        }
    }
}
```

When you need to pass additional arguments to transmutator, use the list of
name and additional parameters instead of string with name:

```json
{
    ...,
    "fields": {
        "my_field": {
            "validators": [
                "simple_transmutator",
                ["complex_transmutator", 42, "hello_world"]
            ]
        }
    }
}
```

In the last example, first transmutator will be called as
`simple_transmutator(field)`, while second one as `complex_transmutator(field,
42, "hello_world")`

To pass into transmutator *the value* of the current field, pass `"$self"` as
an argument. In the similar manner, `"$field_name"` sends value of the
`field_name` into transmutator:

```json
{
    ...,
    "fields": {
        "my_field": {
            "validators": [
                ["complex_transmutator", "$self", "$other_field", 0]
            ]
        },
        "other_field": {"default": 42}
    }
}
```

In this case, transmutator will be called as `complex_transmutator(field,
<VALUE OF CURRENT FIELD>, <VALUE OF other_field>, 0)`.

Transmutator modifies field in place and returns the whole field when job is done.

ckanext-transmute contains a number of transmutators that can be used without
additional configuration. And if you need more, you can define a custom
transmutator with the `ITransmute ` interface.

::: transmute.transmutators
    options:
        show_root_heading: false
