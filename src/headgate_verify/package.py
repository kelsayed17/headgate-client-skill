# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""Discovery of the client packages under the paths given on the command line."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

_SKIPPED = frozenset({"tests", ".venv"})


@dataclass(frozen=True)
class Package:
    """A directory holding a ``client.py`` and the python modules beside it."""

    root: Path
    modules: tuple[Path, ...]


def _package(root: Path) -> Package:
    return Package(root, tuple(sorted(root.glob("*.py"))))


def _roots(path: Path) -> set[Path]:
    if path.is_file():
        return {path.parent} if path.name == "client.py" else set()
    roots: set[Path] = set()
    for directory, names, files in os.walk(path):
        names[:] = [name for name in names if name not in _SKIPPED and not name.startswith(".")]
        if "client.py" in files:
            roots.add(Path(directory))
    return roots


def find_packages(paths: Sequence[Path]) -> list[Package]:
    """Return each client package under ``paths`` once, sorted by root."""
    roots = set().union(*(_roots(path) for path in paths)) if paths else set()
    return [_package(root) for root in sorted(roots)]
