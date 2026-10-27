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


def _package(tmp_path: Path) -> Path:
    """Return a directory holding one client package, so a run has something to check."""
    (tmp_path / "lda").mkdir()
    (tmp_path / "lda" / "client.py").write_text("")
    return tmp_path


def test_path_without_package_is_usage_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Every path under which no client package is found is named on stderr, and the run is a usage error."""
    empty, other = tmp_path / "empty", tmp_path / "other"
    empty.mkdir()
    other.mkdir()
    (other / "models.py").write_text("")
    assert cli.main([str(empty), str(other)]) == USAGE_ERROR
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == (
        f"headgate-verify: no client package (a directory holding client.py) under {empty}\n"
        f"headgate-verify: no client package (a directory holding client.py) under {other}\n"
    )


def test_one_empty_path_among_packages_is_usage_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """A path with no package fails the run even when another path holds one."""
    _package(tmp_path)
    empty = tmp_path / "empty"
    empty.mkdir()
    assert cli.main([str(tmp_path / "lda"), str(empty)]) == USAGE_ERROR
    assert str(empty) in capsys.readouterr().err


def test_every_missing_path_is_named(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Each path that does not exist is named on stderr."""
    assert cli.main([str(tmp_path / "a"), str(tmp_path / "b")]) == USAGE_ERROR
    err = capsys.readouterr().err
    assert f"no such path: {tmp_path / 'a'}" in err
    assert f"no such path: {tmp_path / 'b'}" in err


def test_clean_run_counts_packages_on_stderr(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A clean run prints nothing on stdout, says how many packages it checked on stderr, and exits 0."""
    _package(tmp_path)
    (tmp_path / "sec").mkdir()
    (tmp_path / "sec" / "client.py").write_text("")
    monkeypatch.setattr(engine, "verify", lambda _paths, _config=None: [])
    assert cli.main([str(tmp_path)]) == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "checked 2 package(s)\n"


def test_json_format_lists_findings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The json format prints one object per finding, its fix included, and an error exits 1."""
    finding = Finding("some-rule", tmp_path / "client.py", 3, "bad", "error", "do this")
    monkeypatch.setattr(engine, "verify", lambda _paths, _config=None: [finding])
    assert cli.main(["--format", "json", str(_package(tmp_path))]) == 1
    assert json.loads(capsys.readouterr().out) == [
        {
            "rule": "some-rule",
            "path": str(tmp_path / "client.py"),
            "line": 3,
            "message": "bad",
            "severity": "error",
            "fix": "do this",
        },
    ]


def test_text_format_renders_findings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The text format prints one line per finding, its severity included, and its fix indented on the next."""
    fixed = Finding("some-rule", tmp_path / "client.py", 3, "bad", "error", "do this")
    bare = Finding("other-rule", tmp_path / "client.py", 4, "meh", "warning")
    monkeypatch.setattr(engine, "verify", lambda _paths, _config=None: [fixed, bare])
    cli.main([str(_package(tmp_path))])
    assert capsys.readouterr().out == (
        f"{tmp_path / 'client.py'}:3 error some-rule bad\n"
        "    do this\n"
        f"{tmp_path / 'client.py'}:4 warning other-rule meh\n"
    )


def test_warnings_only_exit_zero(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Warnings alone do not fail the run."""
    finding = Finding("some-rule", tmp_path / "client.py", 1, "meh", "warning")
    monkeypatch.setattr(engine, "verify", lambda _paths, _config=None: [finding])
    assert cli.main([str(_package(tmp_path))]) == 0


def test_bad_config_exits_two(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A bad [tool.headgate-verify] table is a usage error naming the key."""
    (tmp_path / "pyproject.toml").write_text("[tool.headgate-verify]\nbogus = []\n")
    monkeypatch.chdir(tmp_path)
    assert cli.main([str(tmp_path)]) == USAGE_ERROR
    assert "bogus" in capsys.readouterr().err
