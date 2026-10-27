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
  nothing. Reported at the first import of the flavour, as is a missing or unreadable ``pyproject.toml``.

A package importing neither flavour declares nothing and is not reported.
"""

import tomllib
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from packaging.requirements import InvalidRequirement, Requirement
from packaging.utils import canonicalize_name

from headgate_verify.config import nearest_pyproject
from headgate_verify.finding import Finding

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from ast_grep_py import SgNode, SgRoot

    from headgate_verify.config import Config
    from headgate_verify.package import Package

type Flavour = Literal["msgspec", "pydantic"]

RULE = "one-flavour"
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


def _imported(name: SgNode) -> str:
    """Return the dotted name an import names, without its ``as`` alias."""
    original = name.field("name") if name.kind() == "aliased_import" else name
    return "" if original is None else original.text()


def _flavours_of_statement(statement: SgNode) -> Iterator[Flavour]:
    names = [_imported(name) for name in statement.field_children("name")]
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


def _imports(modules: dict[Path, SgRoot]) -> list[_Import]:
    """Return every flavour import of the package, in path then line order."""
    found = [
        _Import(path, statement.range().start.line + 1, flavour)
        for path, root in modules.items()
        for statement in root.root().find_all(any=[{"kind": "import_statement"}, {"kind": "import_from_statement"}])
        for flavour in _flavours_of_statement(statement)
    ]
    return sorted(found)


def detect_flavour(modules: dict[Path, SgRoot]) -> Flavour | None:
    """Return the one flavour the modules import, or None when they import neither or both."""
    flavours = {found.flavour for found in _imports(modules)}
    return next(iter(flavours)) if len(flavours) == 1 else None


def _requirements(data: dict[str, object]) -> Iterator[object]:
    project = data.get("project")
    if isinstance(project, dict):
        yield from project.get("dependencies", [])
        optional = project.get("optional-dependencies", {})
        if isinstance(optional, dict):
            for group in optional.values():
                yield from group if isinstance(group, list) else []
    groups = data.get("dependency-groups", {})
    if isinstance(groups, dict):
        for group in groups.values():
            yield from group if isinstance(group, list) else []


def _declares(data: dict[str, object], flavour: Flavour) -> bool:
    for entry in _requirements(data):
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


def _extra_problem(pkg: Package, flavour: Flavour) -> str | None:
    pyproject = nearest_pyproject(pkg.root)
    if pyproject is None:
        return f"the package imports {flavour} but no pyproject.toml at or above it declares headgate[{flavour}]"
    try:
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as error:
        return f"{pyproject} is not valid TOML ({error}), so it cannot declare headgate[{flavour}]"
    if _declares(data, flavour):
        return None
    return (
        f"the package imports {flavour} but {pyproject} does not declare headgate[{flavour}] in "
        "[project].dependencies, [project.optional-dependencies] or [dependency-groups]"
    )


def check(pkg: Package, modules: dict[Path, SgRoot], config: Config) -> list[Finding]:
    """Return the ``one-flavour`` findings of ``pkg``."""
    del config
    imports = _imports(modules)
    if not imports:
        return []
    first = imports[0]
    other = next((found for found in imports if found.flavour != first.flavour), None)
    if other is not None:
        return [
            Finding(
                RULE,
                other.path,
                other.line,
                f"the package imports both flavours: {first.flavour} at {first.path.name}:{first.line} and "
                f"{other.flavour} here; a client package uses one",
                "error",
            )
        ]
    problem = _extra_problem(pkg, first.flavour)
    return [] if problem is None else [Finding(RULE, first.path, first.line, problem, "error")]
