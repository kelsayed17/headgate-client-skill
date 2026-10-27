# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""Tests for finding ordering and package discovery."""

from pathlib import Path

from headgate_verify.engine import verify
from headgate_verify.finding import Finding
from headgate_verify.package import find_packages


def _touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("")


def test_directory_of_packages_checks_each_once(tmp_path: Path) -> None:
    """A directory yields every package below it once; hidden, venv and test trees are skipped."""
    for rel in ("a/client.py", "b/client.py", "b/sub/client.py", ".venv/x/client.py", "tests/t/client.py"):
        _touch(tmp_path / rel)
    roots = [package.root for package in find_packages([tmp_path])]
    assert roots == [tmp_path / "a", tmp_path / "b", tmp_path / "b" / "sub"]
    assert [package.root for package in find_packages([tmp_path / "a" / "client.py", tmp_path / "a"])] == [
        tmp_path / "a",
    ]


def test_package_lists_its_modules(tmp_path: Path) -> None:
    """A package holds the python files directly in its directory."""
    for name in ("client.py", "models.py", "notes.txt"):
        _touch(tmp_path / "a" / name)
    (package,) = find_packages([tmp_path])
    assert package.modules == (tmp_path / "a" / "client.py", tmp_path / "a" / "models.py")


def test_findings_sort_by_path_line_rule() -> None:
    """Findings order by path, then line, then rule; render is path:line rule message."""
    late = Finding("b", Path("a.py"), 2, "m", "error")
    early = Finding("z", Path("a.py"), 1, "m", "error")
    other = Finding("a", Path("a.py"), 2, "m", "warning")
    assert sorted([late, early, other]) == [early, other, late]
    assert early.render() == "a.py:1 z m"


def test_verify_without_packages_finds_nothing(tmp_path: Path) -> None:
    """A path holding no client package yields no findings."""
    assert verify([tmp_path]) == []
