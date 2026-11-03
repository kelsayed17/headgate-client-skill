# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""``package-layout``: a client package has the files the conventions name.

Reported:

* no ``__init__.py``; an ``__init__.py`` holding no docstring; any statement in it after the docstring (a re-export,
  an ``__all__``, an import), one finding per statement. Comments are allowed;
* no ``models.py`` in a package that declares a model: a class based on ``Struct`` or ``BaseModel`` (a bare
  ``TypedDict`` does not count) defined in a module other than ``models.py``, or an import from a ``models`` module.
  A package with no model (a client that returns raw bytes or nothing) needs none. No
  ``docs_paths.json``: it sits in the package, so it ships in the wheel as package data;
* a ``docs_paths.json`` that is not valid JSON or breaks the docs snapshot schema (``headgate_verify.naming``), at its
  line 1. Whether the client's names follow it is the client's own ``test_method_names.py``'s business;
* no tests directory holding both a client test and ``test_method_names.py``. A client test is ``test_client.py`` or
  one file per host, ``test_client_<host>.py`` (``test_client_*.py``). The tests directory is
  ``<package>/tests/``, ``tests/<package name>/`` beside the package (``<package>/../tests/<package name>/``, as the
  conventions draw it; ruling R14), or ``tests/<package name>/`` under the project root, the directory of the nearest
  ``pyproject.toml`` at or above the package (with no ``pyproject.toml`` only the first two are looked for). When one
  of them exists, each file it lacks is named;
* a public top-level ``*.py`` file of the package that is neither ``__init__``, ``client``, ``models`` nor
  ``pagination``, and not declared in ``package-modules``, at its own line 1 (so an allow comment there exempts it).
  ``_``-prefixed files, subdirectories and files that are not ``.py`` are not read;
* a call to ``self.paginate(...)`` in any module of the package with no ``pagination.py`` beside it, at the call.

A missing file is reported at line 1 of ``client.py``, so an allow comment above its first statement exempts it. An
``__init__.py`` that does not parse is reported as ``parse-error`` and not read here.
"""

from typing import TYPE_CHECKING

from headgate_verify.config import CONVENTIONAL_MODULES, nearest_pyproject
from headgate_verify.finding import Rule
from headgate_verify.snapshot import SnapshotError, load_snapshot
from headgate_verify.syntax import bases, classes, line, statements, string_prefix

if TYPE_CHECKING:
    from pathlib import Path

    from ast_grep_py import SgNode

    from headgate_verify.config import Config
    from headgate_verify.finding import Finding
    from headgate_verify.package import Package
    from headgate_verify.parsing import Modules

RULE = Rule(
    id="package-layout",
    severity="error",
    fix="Add the file the finding names: a docstring-only `__init__.py`, `models.py`, a schema-valid "
    "`docs_paths.json`, `test_client.py` (or one `test_client_<host>.py` per host) and `test_method_names.py` in the "
    "tests directory, and `pagination.py` beside a paged client; or declare a project module in `package-modules`.",
)
_INIT = "__init__.py"
_DOCS = "docs_paths.json"
_MODELS = "models.py"
_REQUIRED = (_DOCS,)
_CLIENT_TESTS = ("test_client.py", "test_client_*.py")
_METHOD_NAMES = "test_method_names.py"
_MODEL_BASES = ("Struct", "BaseModel")
_PAGINATION = "pagination.py"


def _missing(pkg: Package, message: str) -> Finding:
    """Return a finding for something the package lacks, at line 1 of its ``client.py``."""
    return RULE.finding(pkg.root / "client.py", 1, message)


def _is_docstring(statement: SgNode) -> bool:
    """Return whether ``statement`` is a bare plain string literal (an f- or t-string is no docstring)."""
    children = statement.named_children()
    if statement.kind() != "expression_statement" or len(children) != 1:
        return False
    prefix = string_prefix(children[0])
    return prefix is not None and not any(letter in prefix for letter in "ft")


def _check_init(pkg: Package, modules: Modules) -> list[Finding]:
    path = pkg.root / _INIT
    if not path.is_file():
        return [_missing(pkg, f"the package {pkg.root.name} has no {_INIT}")]
    root = modules.get(path)
    if root is None:
        return []
    body = statements(root.root())
    has_docstring = bool(body) and _is_docstring(body[0])
    findings = (
        [] if has_docstring else [RULE.finding(path, 1, f"{_INIT} holds no docstring; it holds a docstring only")]
    )
    findings += [
        RULE.finding(
            path,
            line(statement),
            f"{_INIT} holds a docstring only; import from the module that defines a name, never through a re-export",
        )
        for statement in body[1 if has_docstring else 0 :]
    ]
    return findings


def _imports_models(statement: SgNode) -> bool:
    module = statement.field("module_name")
    if module is not None and module.text().rsplit(".", 1)[-1] == "models":
        return True
    names = [child for child in statement.children() if child.kind() in ("dotted_name", "aliased_import")]
    return any(child.text().split()[0].split(".")[0] == "models" for child in names if child != module)


def _is_model_base(base: SgNode) -> bool:
    return base.text().split("[", 1)[0].rsplit(".", 1)[-1] in _MODEL_BASES


def _declares_model(pkg: Package, modules: Modules) -> bool:
    """Return whether a module besides ``models.py`` defines a model class or imports from ``models``."""
    for path, root in modules.items():
        if path == pkg.root / _MODELS:
            continue
        if any(_imports_models(statement) for statement in root.root().find_all(kind="import_from_statement")):
            return True
        if any(_is_model_base(base) for _, node, _ in classes({path: root}) for base in bases(node)):
            return True
    return False


def _check_required(pkg: Package, modules: Modules) -> list[Finding]:
    names = list(_REQUIRED)
    if _declares_model(pkg, modules):
        names.insert(0, _MODELS)
    return [
        _missing(pkg, f"the package {pkg.root.name} has no {name}") for name in names if not (pkg.root / name).is_file()
    ]


def _check_snapshot(pkg: Package) -> list[Finding]:
    path = pkg.root / _DOCS
    if not path.is_file():
        return []
    try:
        load_snapshot(path)
    except SnapshotError as error:
        return [RULE.finding(path, 1, f"{_DOCS} is not a valid docs snapshot: {error}")]
    return []


def _test_dirs(pkg: Package) -> list[Path]:
    candidates = [pkg.root / "tests", pkg.root.parent / "tests" / pkg.root.name]
    pyproject = nearest_pyproject(pkg.root)
    if pyproject is not None:
        candidates.append(pyproject.parent / "tests" / pkg.root.name)
    return list(dict.fromkeys(candidates))


def _client_tests(directory: Path) -> bool:
    return any(path.is_file() for pattern in _CLIENT_TESTS for path in directory.glob(pattern))


def _has_tests(directory: Path) -> bool:
    return _client_tests(directory) and (directory / _METHOD_NAMES).is_file()


def _check_tests(pkg: Package) -> list[Finding]:
    candidates = _test_dirs(pkg)
    existing = [directory for directory in candidates if directory.is_dir()]
    if any(_has_tests(directory) for directory in existing):
        return []
    if not existing:
        looked = " or ".join(str(directory) for directory in candidates)
        return [_missing(pkg, f"the package {pkg.root.name} has no tests directory (looked for {looked})")]
    directory = existing[0]
    return [
        _missing(pkg, f"the tests directory {directory} has no {name}")
        for name, present in (
            ("test_client.py (or a test_client_<host>.py per host)", _client_tests(directory)),
            (_METHOD_NAMES, (directory / _METHOD_NAMES).is_file()),
        )
        if not present
    ]


def _check_pagination(pkg: Package, modules: Modules) -> list[Finding]:
    if (pkg.root / _PAGINATION).is_file():
        return []
    for path, root in sorted(modules.items()):
        call = root.root().find(pattern="self.paginate($$$)")
        if call is not None:
            return [
                RULE.finding(
                    path,
                    line(call),
                    f"the package calls self.paginate but has no {_PAGINATION}; its pagers and page budgets live there",
                )
            ]
    return []


def _check_modules(pkg: Package, config: Config) -> list[Finding]:
    """Report, at line 1 of the file, each public top-level module that is neither conventional nor declared."""
    declared = {entry for entry in config.package_modules if "/" not in entry}
    declared |= {
        entry.partition("/")[2] for entry in config.package_modules if entry.partition("/")[0] == pkg.root.name
    }
    return [
        RULE.finding(
            path,
            1,
            f"{path.name} is not a module the conventions name ({_conventional()}); declare it in "
            "[tool.headgate-verify] package-modules, or make it private with a leading underscore",
        )
        for path in sorted(pkg.root.glob("*.py"))
        if path.is_file()
        and not path.name.startswith("_")
        and path.name not in CONVENTIONAL_MODULES
        and path.name not in declared
    ]


def _conventional() -> str:
    return ", ".join(name.removesuffix(".py") for name in sorted(CONVENTIONAL_MODULES))


def check(pkg: Package, modules: Modules, config: Config) -> list[Finding]:
    """Return the ``package-layout`` findings of ``pkg``."""
    return [
        *_check_init(pkg, modules),
        *_check_required(pkg, modules),
        *_check_snapshot(pkg),
        *_check_tests(pkg),
        *_check_pagination(pkg, modules),
        *_check_modules(pkg, config),
    ]
