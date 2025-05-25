import re
import shutil
import subprocess
import sys
from argparse import ArgumentParser, ArgumentTypeError, BooleanOptionalAction
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Optional, TypedDict

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
DEFAULT_EXCLUDED_PACKAGES: Final = ["mypy", "mypy-extensions", "tomli", "typing-extensions"]

RE_UV_GROUP_NAME: Final = re.compile(r"^[a-z0-9](?:[a-z0-9._-]*[a-z0-9])?$", re.IGNORECASE)
RE_PACKAGE_NAME: Final = re.compile(r"^[a-zA-Z0-9]+([-_.]?[a-zA-Z0-9]+)*$")


@dataclass
class YamlConfig:
    width: Final[int] = DEFAULT_YAML_LINE_LENGTH
    indent: Final[int] = DEFAULT_YAML_INDENT
    default_flow_style: Final[bool] = DEFAULT_YAML_FLOW_STYLE
    sort_keys: Final[bool] = DEFAULT_YAML_SORT_KEYS


def validate_group(group: str) -> str:
    if not RE_UV_GROUP_NAME.fullmatch(group):
        raise ArgumentTypeError(f"{group} is not a valid UV group name")
    return group


def validate_package(package: str) -> str:
    if not RE_PACKAGE_NAME.fullmatch(package):
        raise ArgumentTypeError(f"{package} is not a package name")
    return package


def valid_file(path_str: str) -> Path:
    path = Path(path_str)
    if not path.is_file():
        raise ArgumentTypeError(f"{path_str} is not a file")

    return path


def get_dependencies(
    groups: Sequence[str], excluded_packages: Sequence[str], pyproject_toml_path: Optional[Path] = None
) -> list[str]:
    parameter = [
        "uv",
        "export",
        "--no-emit-project",
        "--no-editable",
        "--no-hashes",
        "--no-header",
        "--quiet",
        "--no-default-groups",
        "--no-annotate",
    ]
    parameter.extend([f"--group={group}" for group in groups])
    parameter.extend([f"--no-emit-package={package}" for package in excluded_packages])
    if pyproject_toml_path:
        parameter.append(f"--config-file={pyproject_toml_path}")

    result = subprocess.run(parameter, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    return list(filter(None, result.stdout.splitlines()))


def update_additional_dependencies(config: PreCommitConfig, deps: Sequence[str]) -> PreCommitConfig:
    for repo in config["repos"]:
        for hook in repo.get("hooks", []):
            if hook["id"] == "mypy":
                hook["additional_dependencies"] = deps
                return config

    raise RuntimeError("mypy hook not found in pre-commit config")


def update_mypy_hook(
    pre_commit_config_path: Path,
    groups: Sequence[str],
    excluded_packages: Sequence[str],
    yaml_config: YamlConfig,
    pyproject_toml_path: Optional[Path] = None,
) -> None:
    deps = get_dependencies(groups=groups, excluded_packages=excluded_packages, pyproject_toml_path=pyproject_toml_path)
    config = yaml.safe_load(pre_commit_config_path.read_text())
    pre_commit_config_path.write_text(
        yaml.dump(
            update_additional_dependencies(config=config, deps=deps),
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
        type=validate_group,
        action="append",
        help=f"Dependency group to include. Can be used multiple times (default: {', '.join(DEFAULT_GROUPS)})",
        dest="groups",
        metavar="GROUP",
    )
    parser.add_argument(
        "-c",
        "--pre-commit-config-path",
        type=valid_file,
        default=DEFAULT_CONFIG_PATH,
        help=f"Path to .pre-commit-config.yaml (default: {DEFAULT_CONFIG_PATH})",
    )
    parser.add_argument(
        "-p",
        "--pyproject-path",
        type=valid_file,
        help="Path to pyproject.toml. Only needed if not in project root.",
    )
    parser.add_argument(
        "--excluded-package",
        type=validate_package,
        action="append",
        help=f"Package excluded in the additional_dependencies. Can be used multiple times "
        f"(default: {', '.join(DEFAULT_EXCLUDED_PACKAGES)})",
        dest="excluded_packages",
        metavar="PACKAGE",
    )
    parser.add_argument(
        "-x",
        "--extra-excluded-package",
        type=validate_package,
        action="append",
        help="Additional package excluded from additional_dependencies. Extends the --excluded-package option. "
        "Can be used multiple times.",
        dest="extra_excluded_packages",
        metavar="PACKAGE",
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

    groups = args.groups or DEFAULT_GROUPS
    excluded_packages = args.excluded_packages or DEFAULT_EXCLUDED_PACKAGES
    extra_excluded_packages = args.extra_excluded_packages
    if extra_excluded_packages:
        excluded_packages.extend(args.extra_excluded_packages)

    if shutil.which("uv") is None:
        print("uv not found", file=sys.stderr)
        print("Please install uv and try again.", file=sys.stderr)
        sys.exit(1)

    result = subprocess.run(["uv", "--version"], capture_output=True, text=True, check=True)
    major, minor, patch = tuple(map(int, result.stdout.split()[1].split(".")))
    if major == 0 and minor < 7:
        print("version of uv needs to >= 0.7.0", file=sys.stderr)
        sys.exit(1)

    yaml_config = YamlConfig(
        width=args.yaml_width,
        indent=args.yaml_indent,
        default_flow_style=args.yaml_default_flow_style,
        sort_keys=args.yaml_sort_keys,
    )

    try:
        update_mypy_hook(
            pre_commit_config_path=args.pre_commit_config_path,
            groups=groups,
            excluded_packages=excluded_packages,
            yaml_config=yaml_config,
            pyproject_toml_path=args.pyproject_path,
        )
    except RuntimeError as e:
        print(e, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
