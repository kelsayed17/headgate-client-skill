# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""Helpers the tests share for building packages on disk."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path


def write(root: Path, name: str, text: str = "") -> Path:
    """Write ``text`` to ``root / name``, creating the directories it needs, and return the path."""
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def write_all(root: Path, files: Mapping[str, str]) -> None:
    """Write each ``name: text`` of ``files`` under ``root``, creating the directories each needs."""
    for name, text in files.items():
        write(root, name, text)
