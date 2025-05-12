# /// script
# dependencies = [
#   "pyyaml",
#   "typing-extensions; python_version < '3.11'"
# ]
# ///
import shutil
import subprocess
import sys
from argparse import ArgumentParser, BooleanOptionalAction
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final, TypedDict

import yaml

if sys.version_info >= (3, 11):
    from typing import NotRequired
else:
    from typing_extensions import NotRequired


class PreCommitConfigRepoHook(TypedDict):
    id: str
    additional_dependencies: NotRequired[Sequence[str]]


class PreCommitConfigRepo(TypedDict):
    hooks: Sequence[PreCommitConfigRepoHook]


class PreCommitConfig(TypedDict):
    repos: Sequence[PreCommitConfigRepo]


DEFAULT_YAML_LINE_LENGTH: Final = 120
DEFAULT_YAML_INDENT: Final = 2
DEFAULT_YAML_FLOW_STYLE: Final = False
DEFAULT_YAML_SORT_KEYS: Final = False
DEFAULT_CONFIG_PATH: Final = Path(".pre-commit-config.yaml")
DEFAULT_GROUPS: Final = ["mypy"]
DEFAULT_PYPROJECT_PATH: Final = Path("pyproject.toml")


@dataclass
class YamlConfig:
    width: int = DEFAULT_YAML_LINE_LENGTH
    indent: int = DEFAULT_YAML_INDENT
    default_flow_style: bool = DEFAULT_YAML_FLOW_STYLE
    sort_keys: bool = DEFAULT_YAML_SORT_KEYS


def get_dependencies(pyproject_toml_path: Path, groups: Sequence[str]) -> list[str]:
    parameter = ["uv", "pip", "compile", str(pyproject_toml_path.resolve().absolute()), "--no-header", "--quiet"]
    parameter.extend([item for group in groups for item in ("--group", group)])
    result = subprocess.run(parameter, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    deps = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        package = line.split("==")[0]
        if package in [
            "mypy",
            "mypy-extensions",
            "tomli",  # python < 3.11
            "typing-extensions",
        ]:
            continue

        # Remove version specifiers if necessary
        deps.append(line.split()[0])
    return deps


def update_additional_dependencies(config: PreCommitConfig, deps: Sequence[str]) -> PreCommitConfig:
    for repo in config["repos"]:
        for hook in repo.get("hooks", []):
            if hook["id"] == "mypy":
                hook["additional_dependencies"] = deps
                return config

    raise RuntimeError("mypy hook not found in pre-commit config")


def update_mypy_hook(
    pyproject_toml_path: Path, pre_commit_config_path: Path, groups: Sequence[str], yaml_config: YamlConfig
) -> None:
    deps = get_dependencies(pyproject_toml_path=pyproject_toml_path, groups=groups)
    config = yaml.safe_load(pre_commit_config_path.read_text())
    pre_commit_config_path.write_text(
        yaml.dump(
            update_additional_dependencies(config, deps),
            default_flow_style=yaml_config.default_flow_style,
            sort_keys=yaml_config.sort_keys,
            indent=yaml_config.indent,
            width=yaml_config.width,
        )
    )


def main() -> None:
    parser = ArgumentParser()
    parser.description = "Update `mypy` hook in .pre-commit-config.yml with uv.lock file. uv must be installed."
    parser.add_argument(
        "-g",
        "--group",
        action="append",
        help=f"dependency group to include. Can be used multiple times (default: {DEFAULT_GROUPS})",
    )
    parser.add_argument(
        "-p",
        "--pyproject-path",
        default=DEFAULT_PYPROJECT_PATH,
        type=Path,
        help=f"path to pyproject.toml (default: {DEFAULT_PYPROJECT_PATH})",
    )
    parser.add_argument(
        "-c",
        "--pre-commit-config-path",
        default=DEFAULT_CONFIG_PATH,
        type=Path,
        help=f"path to .pre-commit-config.yaml (default: {DEFAULT_CONFIG_PATH})",
    )
    parser.add_argument(
        "--yaml-width",
        type=int,
        default=DEFAULT_YAML_LINE_LENGTH,
        help=f"maximum width of yaml output (default: {DEFAULT_YAML_LINE_LENGTH})",
    )
    parser.add_argument(
        "--yaml-indent",
        type=int,
        default=DEFAULT_YAML_INDENT,
        help=f"number of spaces to indent (default: {DEFAULT_YAML_INDENT})",
    )
    parser.add_argument(
        "--yaml-default-flow-style",
        action=BooleanOptionalAction,
        default=DEFAULT_YAML_FLOW_STYLE,
        help="use default flow style",
    )
    parser.add_argument(
        "--yaml-sort-keys",
        action=BooleanOptionalAction,
        default=DEFAULT_YAML_SORT_KEYS,
        help="sort keys in yaml output",
    )
    args = parser.parse_args()

    groups = args.group or DEFAULT_GROUPS

    if shutil.which("uv") is None:
        print("uv not found", file=sys.stderr)
        print("Please install uv and try again.", file=sys.stderr)
        sys.exit(1)

    result = subprocess.run(["uv", "--version"], capture_output=True, text=True, check=True)
    major, minor, patch = tuple(map(int, result.stdout.split()[1].split(".")))
    if major == 0 and minor < 6:
        print("version of uv needs to >= 0.6.0", file=sys.stderr)
        sys.exit(1)

    yaml_config = YamlConfig(
        width=args.yaml_width,
        indent=args.yaml_indent,
        default_flow_style=args.yaml_default_flow_style,
        sort_keys=args.yaml_sort_keys,
    )

    try:
        update_mypy_hook(
            pyproject_toml_path=args.pyproject_path,
            pre_commit_config_path=args.pre_commit_config_path,
            groups=groups,
            yaml_config=yaml_config,
        )
    except RuntimeError as e:
        print(e, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
