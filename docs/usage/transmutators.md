Transmutators are similar to CKAN validators. They accept the field and modify
it. But unlike validators, transmutators work with field and have access to the
whole schema definition.

Usually, transmutator is defined as a function with a single argument. This
argument always receives the instance of validated field. It's a dataclass with

* `field_name`: the name of processed field
* `value`: current value of the field
* `type`: the name of the type that contains field definition
* `data`: the whole data dictionary that is currently transmuted

Transmutator modifies field in place and returns the whole field when job is done.


ckanext-transmute contains a number of transmutators that can be used without
additional configuration. And if you need more, you can define a custom
transmutator with the `ITransmute ` interface.

::: transmute.transmutators
    options:
        show_root_heading: false
