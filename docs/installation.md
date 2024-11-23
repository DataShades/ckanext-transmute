# Installation

## Requirements

Compatibility with core CKAN versions:

| CKAN version | Compatible? |
|--------------|-------------|
| 2.9          | no          |
| 2.10         | yes         |
| 2.11         | yes         |
| master       | yes         |


!!! note

    It's recommended to install the extension via pip. If you are using GitHub
    version of the extension, stick to the vX.Y.Z tags to avoid breaking
    changes. Check the [changelog](changelog.md) before upgrading the extension.

## Installation

Install the extension

```sh
pip install ckanext-transmute
```

Add `transmute` to the `ckan.plugins` setting in your CKAN config file.
