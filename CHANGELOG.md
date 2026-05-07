## [2.0.0] - 2026-05-07

BREAKING: requires migration, tsm_transmute doesn't change original data now

### 🐛 Bug Fixes

- Do a original data deepcopy as was stated before

## [1.9.2] - 2026-05-07

Release v1.9.2

### 🐛 Bug Fixes

- Fix tsm_list_mapper to allow using falsy values as a default

## [1.9.1] - 2026-05-07

Release v1.9.1

### 🐛 Bug Fixes

- Fix tsm_mapper to allow using falsy values as a default

## [1.9.0] - 2026-05-07

Release v1.9.0

### 🐛 Bug Fixes

- Fix replace_from and default_from if value is missing in a target data, add get_json_schema

## [1.8.0] - 2025-05-13

Release v1.8.0

### 🚀 Features

- Pre-fields and post-fields added to schema

### 🐛 Bug Fixes

- Add namespace_packages to setup.cfg

### ⚙️ Miscellaneous Tasks

- Flatten logic module
- Apply ruff fixes
- Add docs
- Update transmustartor docs

## [1.7.0] - 2024-10-30

### 🚀 Features

- Add tsm_mapper transmutator
- Add tsm_list_mapper transmutator
- Add named schemas
- Add weight to fields
- Add schema drop_unknown_fields
- Add stop_on_empty transmutator
- Combine default and default_from
- Add map_value transmutator

### 🐛 Bug Fixes

- Tsm_transmute action ignores custom root
- Falsy values cannot be used as default
- Default overrides value

### 💼 Other

- Update tsm_mapping transmutator

### 📚 Documentation

- Update doc, refine typos
- Update tsm_mapping and tsm_list_mapping doc
- Update tsm_mapping and tsm_list_mapping doc, part 2

### 🧪 Testing

- Fix tests, add test budge

### ⚙️ Miscellaneous Tasks

- Add pyproject / remove duplicates from requirements
- Fix test
- Build changelog

