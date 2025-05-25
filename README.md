# Update mypy pre-commit hook

This script uses [`uv`](https://docs.astral.sh/uv) to update the `additional_dependencies` of the
[mypy pre-commit hook](https://github.com/pre-commit/mirrors-mypy).

> **⚠️ WARNING ⚠️**
>
> This will rewrite your `.pre-commit-config.yaml` and you will **lose all comments**.

With `uv export` it will generate a list of _all_ dependencies required to run mypy.
By default, it assumes that an `uv` dependency group, called *mypy*, exists and contains all additional dependencies
(besides the project dependencies) to successfully run type checking.
The group(s) may only contain the direct dependencies. Transitive dependencies are derived by `uv` automatically.

The dependency group(s) can be overwritten by `-g/--group` option.

## Installation

If you have installed `uv` on your machine or is already part of your dependencies you can run
```shell
pip install update-mypy-hook
```
or with uv
```shell
uv add update-mypy-hook --group dev
```

If `uv` is not part of your setup, use the extra
```shell
pip install update-mypy-hook[uv]
```

## Using update-mypy-hook

Run in your python project root folder
```shell
update-mypy-hook --help
```

## Pre-commit hook
Add this to your `.pre-commit-config.yaml`

```yaml
- repo: https://github.com/H4rryK4ne/update-mypy-hook
  rev: 0.1.0
  hooks:
  - id: update-dependency-mypy-hook
    additional_dependencies:
    - uv # if uv is not installed on every developer's system
    args:
    - --extra-excluded-package=some_package
    - --extra-excluded-package=some_other_package
```

### Options:
```text
  -g GROUP, --group GROUP
                        Dependency group to include. Can be used multiple times (default: mypy)
  -c PRE_COMMIT_CONFIG_PATH, --pre-commit-config-path PRE_COMMIT_CONFIG_PATH
                        Path to .pre-commit-config.yaml (default: .pre-commit-config.yaml)
  -p PYPROJECT_PATH, --pyproject-path PYPROJECT_PATH
                        Path to pyproject.toml. Only needed if not in project root.
  --excluded-package PACKAGE
                        Package excluded in the additional_dependencies. Can be used multiple times (default: mypy, mypy-extensions, tomli, typing-extensions)
  -x PACKAGE, --extra-excluded-package PACKAGE
                        Additional package excluded from additional_dependencies. Extends the --excluded-package option. Can be used multiple times.
  --yaml-width YAML_WIDTH
                        maximum width of yaml output (default: 120)
  --yaml-indent YAML_INDENT
                        number of spaces to indent (default: 2)
  --yaml-default-flow-style, --no-yaml-default-flow-style
                        use default flow style (default: False)
  --yaml-sort-keys, --no-yaml-sort-keys
                        sort keys in yaml output (default: False)
```
