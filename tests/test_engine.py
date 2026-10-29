# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""Tests for finding ordering and package discovery."""

from pathlib import Path

import pytest

from headgate_verify import cli
from headgate_verify.checks import models
from headgate_verify.engine import verify
from headgate_verify.finding import Finding
from headgate_verify.package import NoPackageError, find_packages
from tests.helpers import write, write_all


def test_directory_of_packages_checks_each_once(tmp_path: Path) -> None:
    """A directory yields every package below it once; hidden, venv and test trees are skipped."""
    for rel in ("a/client.py", "b/client.py", "b/sub/client.py", ".venv/x/client.py", "tests/t/client.py"):
        write(tmp_path, rel)
    roots = [package.root for package in find_packages([tmp_path])]
    assert roots == [tmp_path / "a", tmp_path / "b", tmp_path / "b" / "sub"]
    assert [package.root for package in find_packages([tmp_path / "a" / "client.py", tmp_path / "a"])] == [
        tmp_path / "a",
    ]


def test_package_lists_its_modules(tmp_path: Path) -> None:
    """A package holds the python files directly in its directory."""
    for name in ("client.py", "models.py", "notes.txt"):
        write(tmp_path / "a", name)
    (package,) = find_packages([tmp_path])
    assert package.modules == (tmp_path / "a" / "client.py", tmp_path / "a" / "models.py")


def test_findings_sort_by_path_line_rule() -> None:
    """Findings order by path, then line, then rule; render is path:line severity rule message."""
    late = Finding("b", Path("a.py"), 2, "m", "error")
    early = Finding("z", Path("a.py"), 1, "m", "error")
    other = Finding("a", Path("a.py"), 2, "m", "warning")
    assert sorted([late, early, other]) == [early, other, late]
    assert early.render() == "a.py:1 error z m"


def test_verify_without_packages_raises(tmp_path: Path) -> None:
    """A path holding no client package is refused, naming every such path, not reported clean."""
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    write(tmp_path / "c" / "lda", "client.py")
    with pytest.raises(NoPackageError) as raised:
        verify([tmp_path / "a", tmp_path / "c", tmp_path / "b"])
    assert raised.value.paths == (tmp_path / "a", tmp_path / "b")


def test_build_directories_are_skipped(tmp_path: Path) -> None:
    """Discovery skips virtualenvs, build output, node_modules and site-packages."""
    for name in ("venv", "build", "dist", "node_modules", "site-packages", "lib/site-packages", "ok"):
        write(tmp_path / name / "x", "client.py")
    assert [package.root for package in find_packages([tmp_path])] == [tmp_path / "ok" / "x"]


_CLEAN_CLIENT = """\
import httpx2
from headgate import AsyncBaseClient, HttpOptions, Rate
from headgate.msgspec import decoder

from .models import Item

BASE_URL = "https://data.example"
MAX_RATE_PER_SEC = 2
ITEM = decoder(Item)


class LdaClient(AsyncBaseClient):
    def __init__(self, transport: httpx2.AsyncBaseTransport | None = None) -> None:
        super().__init__(
            base_url=BASE_URL, rate=Rate.per_second(MAX_RATE_PER_SEC), http=HttpOptions(transport=transport)
        )

    async def get_item(self, item_id: str) -> Item:
        \"\"\"``GET /item/{item_id}`` -- the item.\"\"\"
        return await self.get(t"item/{item_id}", expect=ITEM)


def to_int(text: str) -> int | None:
    try:
        return int(text)
    except ValueError:
        return None
"""


def test_warning_severity_reported(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """A package with only a warning yields it as ``warning`` and the command exits 0."""
    package = tmp_path / "lda"
    files = {
        "__init__.py": '"""The lda client."""\n',
        "client.py": _CLEAN_CLIENT,
        "models.py": "import msgspec\n\n\nclass Item(msgspec.Struct, frozen=True, gc=False):\n    id: str\n",
        "docs_paths.json": '{"source": null, "retrieved": "2026-10-26", "reason": "none", "endpoints": []}\n',
        "pyproject.toml": "[project]\nname = 'x'\ndependencies = ['headgate[msgspec]>=0.7.0']\n",
    }
    write_all(package, files)
    for name in ("test_client.py", "test_method_names.py"):
        write(tmp_path / "tests" / "lda", name)
    findings = verify([package])
    assert [(finding.rule, finding.severity, finding.line) for finding in findings] == [
        ("client-except-needs-review", "warning", 26),
    ], findings
    assert cli.main([str(package)]) == 0
    assert "client-except-needs-review" in capsys.readouterr().out


def test_check_finding_carries_its_fix(tmp_path: Path) -> None:
    """A Python check's findings carry the fix sentence its ``RULE`` registers."""
    write(tmp_path / "lda", "client.py")
    write(tmp_path / "lda", "models.py", "class LdaFiling:\n    pass\n")
    (finding,) = [finding for finding in verify([tmp_path]) if finding.rule == models.RULE.id]
    assert finding.fix == models.RULE.fix
    assert finding.fix
