# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v0.3.0] 2025-12-04

### Added

- option `--no-groups` to disable default group `"mypy"` ([#8](https://github.com/H4rryK4ne/update-mypy-hook/pull/8))
- `uv` as required dependency ([#9](https://github.com/H4rryK4ne/update-mypy-hook/pull/9))

### Changed

- use `ruamel-yaml` instead of `pyyaml` to preserve comments ([#8](https://github.com/H4rryK4ne/update-mypy-hook/pull/8))
- use `uv.find_uv_bin` instead of `shutil.which("uv")` ([#9](https://github.com/H4rryK4ne/update-mypy-hook/pull/9))

### Fixed

- new line after comment ([#12](https://github.com/H4rryK4ne/update-mypy-hook/pull/12))

### Removed

- option `--yaml-sort-keys`, `--no-yaml-sort-keys` as it is not natively supported by `ruamel-yaml` ([#8](https://github.com/H4rryK4ne/update-mypy-hook/pull/8))
- `uv` as extra dependency ([#9](https://github.com/H4rryK4ne/update-mypy-hook/pull/9))

### Security

- update dependencies (2025-12-04)


## [v0.2.0] 2025-06-24

### Changed

- replaced `--pyproject-path` with `--project-path`, fixing the case where `pyproject.toml` is not in the current working directory

## [v0.1.0] - 2025-05-26

### Added

- initial release
