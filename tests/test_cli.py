# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""Tests for the command line."""

import json
from typing import TYPE_CHECKING

from headgate_verify import cli, engine
from headgate_verify.finding import Finding

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

USAGE_ERROR = 2


def test_no_paths_is_usage_error() -> None:
    """Without a path the command is misused."""
    assert cli.main([]) == USAGE_ERROR


def test_missing_path_is_usage_error() -> None:
    """A path that does not exist is a usage error."""
    assert cli.main(["nope/"]) == USAGE_ERROR


def test_clean_dir_exits_zero(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """An empty directory has nothing to report."""
    assert cli.main([str(tmp_path)]) == 0
    assert capsys.readouterr().out == ""


def test_json_format_lists_findings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The json format prints one object per finding and an error exits 1."""
    finding = Finding("some-rule", tmp_path / "client.py", 3, "bad", "error")
    monkeypatch.setattr(engine, "verify", lambda _paths, _config=None: [finding])
    assert cli.main(["--format", "json", str(tmp_path)]) == 1
    assert json.loads(capsys.readouterr().out) == [
        {"rule": "some-rule", "path": str(tmp_path / "client.py"), "line": 3, "message": "bad", "severity": "error"},
    ]


def test_text_format_renders_findings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The text format prints one rendered line per finding."""
    finding = Finding("some-rule", tmp_path / "client.py", 3, "bad", "error")
    monkeypatch.setattr(engine, "verify", lambda _paths, _config=None: [finding])
    cli.main([str(tmp_path)])
    assert capsys.readouterr().out == f"{tmp_path / 'client.py'}:3 some-rule bad\n"


def test_warnings_only_exit_zero(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Warnings alone do not fail the run."""
    finding = Finding("some-rule", tmp_path / "client.py", 1, "meh", "warning")
    monkeypatch.setattr(engine, "verify", lambda _paths, _config=None: [finding])
    assert cli.main([str(tmp_path)]) == 0
