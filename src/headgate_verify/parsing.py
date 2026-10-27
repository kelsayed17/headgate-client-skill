# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""Parsing a package's modules into ast-grep-py trees, once per run, and reporting each module that does not parse.

A module that cannot be read, is not UTF-8, or that Python's own parser or tree-sitter refuses is a ``parse-error``
finding and is left out of the trees every rule and check reads.
"""

import ast
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ast_grep_py import SgRoot

from headgate_verify.finding import Rule

if TYPE_CHECKING:
    from pathlib import Path

    from headgate_verify.finding import Finding
    from headgate_verify.package import Package

type Modules = dict[Path, SgRoot]
"""A package's parsed modules: each path that parses, with its tree."""

LANGUAGE = "python"
"""The ast-grep language every module is parsed as."""

PARSE_ERROR = Rule(
    id="parse-error",
    severity="error",
    fix="Make the module a readable UTF-8 file that Python's own parser accepts; no other rule reads it until then.",
)
"""The finding for a module that does not parse; the engine reports it, never a rule file or check."""


@dataclass(frozen=True)
class ParsedPackage:
    """A package's modules that parse, with their trees, and a ``parse-error`` finding for each one that does not."""

    modules: Modules
    errors: tuple[Finding, ...]


def _parse_error(path: Path, line: int, detail: str) -> Finding:
    return PARSE_ERROR.finding(path, line, f"the module does not parse ({detail}); no other rule read it")


def _read(path: Path) -> str | Finding:
    """Return the module's text, or the ``parse-error`` finding saying why it cannot be read."""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        return _parse_error(path, 1, f"not UTF-8: {error.reason}")
    except OSError as error:
        return _parse_error(path, 1, f"the file cannot be read: {error.strerror or error}")


def _parse(path: Path, text: str) -> SgRoot | Finding:
    """Return the module's tree, or the ``parse-error`` finding saying why there is none."""
    # Python's own parser first: tree-sitter repairs some code Python refuses with a MISSING node, which ast-grep-py
    # cannot see. ast.parse only builds a tree; it neither imports nor executes the module.
    try:
        ast.parse(text, filename=str(path))
    except SyntaxError as error:
        return _parse_error(path, error.lineno or 1, f"syntax error: {error.msg}")
    except ValueError as error:
        return _parse_error(path, 1, str(error))
    except (MemoryError, RecursionError) as error:
        # Too deep or too large for Python's parser: a finding, so one module cannot crash the run.
        return _parse_error(path, 1, f"{type(error).__name__}: too deep or too large for Python's parser")
    root = SgRoot(text, LANGUAGE)
    broken = root.root().find(kind="ERROR")
    if broken is not None:
        return _parse_error(path, broken.range().start.line + 1, "tree-sitter syntax error")
    return root


def parse_package(pkg: Package) -> ParsedPackage:
    """Return the trees of the modules of ``pkg`` that parse, and a ``parse-error`` for each that does not."""
    modules: Modules = {}
    errors: list[Finding] = []
    for path in pkg.modules:
        text = _read(path)
        parsed = text if not isinstance(text, str) else _parse(path, text)
        if isinstance(parsed, SgRoot):
            modules[path] = parsed
        else:
            errors.append(parsed)
    return ParsedPackage(modules, tuple(errors))
