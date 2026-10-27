# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""``one-flavour``: a client package uses one model flavour, and its project declares that flavour's headgate extra.

The flavour is read from the package's imports, at any depth (a ``TYPE_CHECKING`` block counts): ``msgspec`` from
``import msgspec[.x]``, ``from msgspec[.x] import ...``, ``import headgate.msgspec``, ``from headgate.msgspec import
...`` or ``from headgate import msgspec``; ``pydantic`` likewise. Other modules (``msgspecx``, ``pydantic_settings``)
set nothing. Reported:

* a package importing both flavours, at the first import of the second one met (modules in path order);
* a package of one flavour whose nearest ``pyproject.toml`` (at or above the package) does not declare
  ``headgate[<flavour>]``. A requirement on ``headgate`` whose extras include the flavour's (``headgate[msgspec]``,
  ``headgate[curl,msgspec]``) declares it, in ``[project].dependencies``, any list of
  ``[project.optional-dependencies]`` or any list of ``[dependency-groups]``; names and extras compare as PEP 503
  normalised names, and an entry that is not a valid requirement (an ``include-group`` table, a typo) declares
  nothing. Reported at the first import of the flavour, as is a ``pyproject.toml`` that is missing, unreadable, not
  UTF-8 or not valid TOML, or whose ``[project]``, ``[project.optional-dependencies]`` or ``[dependency-groups]`` is
  not a table, or whose requirement list there is not a list.

A package importing neither flavour declares nothing and is not reported.
"""

import tomllib
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from packaging.requirements import InvalidRequirement, Requirement
from packaging.utils import canonicalize_name

from headgate_verify.config import nearest_pyproject
from headgate_verify.finding import Rule
from headgate_verify.syntax import imported_names, line

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from ast_grep_py import SgNode

    from headgate_verify.config import Config
    from headgate_verify.finding import Finding
    from headgate_verify.package import Package
    from headgate_verify.parsing import Modules

type Flavour = Literal["msgspec", "pydantic"]

RULE = Rule(
    id="one-flavour",
    severity="error",
    fix="Use one model flavour (msgspec or pydantic) across the package, and declare `headgate[<flavour>]` in the "
    "nearest pyproject.toml.",
)
_FLAVOURS: tuple[Flavour, ...] = ("msgspec", "pydantic")
_HEADGATE = "headgate"


@dataclass(frozen=True, order=True)
class _Import:
    path: Path
    line: int
    flavour: Flavour


def _flavour_of_module(dotted: str) -> Flavour | None:
    parts = dotted.split(".")
    for flavour in _FLAVOURS:
        if parts[0] == flavour or parts[:2] == [_HEADGATE, flavour]:
            return flavour
    return None


def _flavours_of_statement(statement: SgNode) -> Iterator[Flavour]:
    names = [original for original, _ in imported_names(statement)]
    if statement.kind() == "import_statement":
        modules = names
    else:
        module = statement.field("module_name")
        source = "" if module is None or module.kind() == "relative_import" else module.text()
        modules = [source, *(f"{source}.{name}" for name in names if source == _HEADGATE)]
    for dotted in modules:
        flavour = _flavour_of_module(dotted)
        if flavour is not None:
            yield flavour


def _imports(modules: Modules) -> list[_Import]:
    """Return every flavour import of the package, in path then line order."""
    found = [
        _Import(path, line(statement), flavour)
        for path, root in modules.items()
        for statement in root.root().find_all(any=[{"kind": "import_statement"}, {"kind": "import_from_statement"}])
        for flavour in _flavours_of_statement(statement)
    ]
    return sorted(found)


def detect_flavour(modules: Modules) -> Flavour | None:
    """Return the one flavour the modules import, or None when they import neither or both."""
    flavours = {found.flavour for found in _imports(modules)}
    return next(iter(flavours)) if len(flavours) == 1 else None


class _MalformedError(ValueError):
    """A table or list of the pyproject that should hold requirements has another shape."""

    def __init__(self, where: str, shape: str) -> None:
        super().__init__(f"{where} is not a {shape}")


def _table(value: object, where: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise _MalformedError(where, "table")
    return {str(key): item for key, item in value.items()}


def _list(value: object, where: str) -> list[object]:
    if not isinstance(value, list):
        raise _MalformedError(where, "list")
    items: list[object] = list(value)
    return items


def _requirements(data: dict[str, object]) -> list[object]:
    """Return every entry of R4's three requirement places; raise ``_MalformedError`` for a misshapen container."""
    entries: list[object] = []
    project = _table(data.get("project", {}), "[project]")
    entries.extend(_list(project.get("dependencies", []), "[project].dependencies"))
    optional = _table(project.get("optional-dependencies", {}), "[project.optional-dependencies]")
    for name, group in optional.items():
        entries.extend(_list(group, f"[project.optional-dependencies].{name}"))
    groups = _table(data.get("dependency-groups", {}), "[dependency-groups]")
    for name, group in groups.items():
        entries.extend(_list(group, f"[dependency-groups].{name}"))
    return entries


def _declares(entries: list[object], flavour: Flavour) -> bool:
    for entry in entries:
        if not isinstance(entry, str):
            continue
        try:
            requirement = Requirement(entry)
        except InvalidRequirement:
            continue
        extras = {canonicalize_name(extra) for extra in requirement.extras}
        if canonicalize_name(requirement.name) == _HEADGATE and flavour in extras:
            return True
    return False


def _entries(pyproject: Path) -> list[object] | str:
    """Return the requirement entries of ``pyproject``, or why it cannot be read for them."""
    try:
        text = pyproject.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        return f"{pyproject} is not UTF-8 ({error.reason})"
    except OSError as error:
        return f"{pyproject} cannot be read ({error.strerror or error})"
    try:
        return _requirements(tomllib.loads(text))
    except tomllib.TOMLDecodeError as error:
        return f"{pyproject} is not valid TOML ({error})"
    except _MalformedError as error:
        return f"{pyproject}: {error}"


def _extra_problem(pkg: Package, flavour: Flavour) -> str | None:
    pyproject = nearest_pyproject(pkg.root)
    if pyproject is None:
        return f"the package imports {flavour} but no pyproject.toml at or above it declares headgate[{flavour}]"
    entries = _entries(pyproject)
    if isinstance(entries, str):
        return f"{entries}, so it cannot declare headgate[{flavour}]"
    if _declares(entries, flavour):
        return None
    return (
        f"the package imports {flavour} but {pyproject} does not declare headgate[{flavour}] in "
        "[project].dependencies, [project.optional-dependencies] or [dependency-groups]"
    )


def check(pkg: Package, modules: Modules, config: Config) -> list[Finding]:
    """Return the ``one-flavour`` findings of ``pkg``."""
    del config
    imports = _imports(modules)
    if not imports:
        return []
    first = imports[0]
    other = next((found for found in imports if found.flavour != first.flavour), None)
    if other is not None:
        return [
            RULE.finding(
                other.path,
                other.line,
                f"the package imports both flavours: {first.flavour} at {first.path.name}:{first.line} and "
                f"{other.flavour} here; a client package uses one",
            )
        ]
    problem = _extra_problem(pkg, first.flavour)
    return [] if problem is None else [RULE.finding(first.path, first.line, problem)]
