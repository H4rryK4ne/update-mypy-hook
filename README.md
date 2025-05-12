# Update mypy pre-commit hook

This hook uses [`uv`](docs.astral.sh/uv) to update the "additional dependencies" of the
[mypy pre-commit hook](https://github.com/pre-commit/mirrors-mypy).

> **WARNING**
>
> This will rewrite your `.pre-commit-config.yaml` and you will lose all comments.

## Using update-mypy-hook

Add this to your `.pre-commit-config.yaml`

```yaml
- repo: .
  rev: 0.1.0
  hooks:
  - id: update-dependency-mypy-hook
```

### Options:
