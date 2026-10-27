# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""``package-layout``: a client package has the files the conventions name.

Reported:

* no ``__init__.py``; an ``__init__.py`` holding no docstring; any statement in it after the docstring (a re-export,
  an ``__all__``, an import), one finding per statement. Comments are allowed;
* no ``models.py``; no ``docs_paths.json`` (its contents are checked elsewhere);
* no tests directory holding both ``test_client.py`` and ``test_method_names.py``. The tests directory is
  ``<package>/tests/``, ``tests/<package name>/`` beside the package (``<package>/../tests/<package name>/``, as the
  conventions draw it; ruling R14), or ``tests/<package name>/`` under the project root, the directory of the nearest
  ``pyproject.toml`` at or above the package (with no ``pyproject.toml`` only the first two are looked for). When one
  of them exists, each file it lacks is named;
* a call to ``self.paginate(...)`` in any module of the package with no ``pagination.py`` beside it, at the call.

A missing file is reported at line 1 of ``client.py``, so an allow comment above its first statement exempts it. An
``__init__.py`` that does not parse is reported as ``parse-error`` and not read here.
"""

from typing import TYPE_CHECKING

from headgate_verify.config import nearest_pyproject
from headgate_verify.finding import Finding

if TYPE_CHECKING:
    from pathlib import Path

    from ast_grep_py import SgNode, SgRoot

    from headgate_verify.config import Config
    from headgate_verify.package import Package

RULE = "package-layout"
_INIT = "__init__.py"
_REQUIRED = ("models.py", "docs_paths.json")
_TESTS = ("test_client.py", "test_method_names.py")
_PAGINATION = "pagination.py"


def _finding(path: Path, line: int, message: str) -> Finding:
    return Finding(RULE, path, line, message, "error")


def _is_docstring(statement: SgNode) -> bool:
    """Return whether ``statement`` is a bare plain string literal (an f- or t-string is no docstring)."""
    children = statement.named_children()
    if statement.kind() != "expression_statement" or len(children) != 1 or children[0].kind() != "string":
        return False
    start = children[0].child(0)
    return start is not None and not any(letter in start.text().lower() for letter in "ft")


def _check_init(pkg: Package, modules: dict[Path, SgRoot], findings: list[Finding]) -> None:
    path = pkg.root / _INIT
    if not path.is_file():
        findings.append(_finding(pkg.root / "client.py", 1, f"the package {pkg.root.name} has no {_INIT}"))
        return
    root = modules.get(path)
    if root is None:
        return
    statements = [child for child in root.root().children() if child.is_named() and child.kind() != "comment"]
    has_docstring = bool(statements) and _is_docstring(statements[0])
    if not has_docstring:
        findings.append(_finding(path, 1, f"{_INIT} holds no docstring; it holds a docstring only"))
    findings.extend(
        _finding(
            path,
            statement.range().start.line + 1,
            f"{_INIT} holds a docstring only; import from the module that defines a name, never through a re-export",
        )
        for statement in statements[1 if has_docstring else 0 :]
    )


def _test_dirs(pkg: Package) -> list[Path]:
    candidates = [pkg.root / "tests", pkg.root.parent / "tests" / pkg.root.name]
    pyproject = nearest_pyproject(pkg.root)
    if pyproject is not None:
        candidates.append(pyproject.parent / "tests" / pkg.root.name)
    return list(dict.fromkeys(candidates))


def _check_tests(pkg: Package, findings: list[Finding]) -> None:
    candidates = _test_dirs(pkg)
    existing = [directory for directory in candidates if directory.is_dir()]
    if any(all((directory / name).is_file() for name in _TESTS) for directory in existing):
        return
    client = pkg.root / "client.py"
    if not existing:
        looked = " or ".join(str(directory) for directory in candidates)
        findings.append(
            _finding(client, 1, f"the package {pkg.root.name} has no tests directory (looked for {looked})")
        )
        return
    directory = existing[0]
    findings.extend(
        _finding(client, 1, f"the tests directory {directory} has no {name}")
        for name in _TESTS
        if not (directory / name).is_file()
    )


def _check_pagination(pkg: Package, modules: dict[Path, SgRoot], findings: list[Finding]) -> None:
    if (pkg.root / _PAGINATION).is_file():
        return
    for path, root in sorted(modules.items()):
        call = root.root().find(pattern="self.paginate($$$)")
        if call is not None:
            findings.append(
                _finding(
                    path,
                    call.range().start.line + 1,
                    f"the package calls self.paginate but has no {_PAGINATION}; its pagers and page budgets live there",
                )
            )
            return


def check(pkg: Package, modules: dict[Path, SgRoot], config: Config) -> list[Finding]:
    """Return the ``package-layout`` findings of ``pkg``."""
    del config
    findings: list[Finding] = []
    _check_init(pkg, modules, findings)
    findings.extend(
        _finding(pkg.root / "client.py", 1, f"the package {pkg.root.name} has no {name}")
        for name in _REQUIRED
        if not (pkg.root / name).is_file()
    )
    _check_tests(pkg, findings)
    _check_pagination(pkg, modules, findings)
    return findings
