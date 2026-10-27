# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""Tests for the project configuration."""

from typing import TYPE_CHECKING

import pytest

from headgate_verify.config import Config, ConfigError, load_config

if TYPE_CHECKING:
    from pathlib import Path


def _write(directory: Path, body: str) -> None:
    (directory / "pyproject.toml").write_text(body)


def test_missing_table_gives_defaults(tmp_path: Path) -> None:
    """A pyproject without the table leaves every default in place."""
    _write(tmp_path, '[project]\nname = "x"\n')
    assert load_config(tmp_path) == Config()


def test_no_pyproject_gives_defaults(tmp_path: Path) -> None:
    """With no pyproject at or above the start, the defaults apply."""
    assert load_config(tmp_path) == Config()


def test_nearest_pyproject_above_start_wins(tmp_path: Path) -> None:
    """The search walks up from the start directory."""
    _write(tmp_path, '[tool.headgate-verify]\npost-reads = ["search"]\n')
    nested = tmp_path / "a" / "b"
    nested.mkdir(parents=True)
    assert load_config(nested).post_reads == frozenset({"search"})


def test_table_overrides_each_key(tmp_path: Path) -> None:
    """Every key in the table replaces its default."""
    _write(
        tmp_path,
        "[tool.headgate-verify]\n"
        'browser-user-agent-packages = ["scraper"]\n'
        'filler-words = ["v1"]\n'
        'post-reads = ["search", "query"]\n'
        'write-name-fragments = ["cancel"]\n',
    )
    assert load_config(tmp_path) == Config(
        browser_user_agent_packages=frozenset({"scraper"}),
        filler_words=frozenset({"v1"}),
        post_reads=frozenset({"search", "query"}),
        write_name_fragments=frozenset({"cancel"}),
    )


def test_unknown_key_is_config_error(tmp_path: Path) -> None:
    """A key the verifier does not know is named in the error."""
    _write(tmp_path, "[tool.headgate-verify]\nfiller_words = []\n")
    with pytest.raises(ConfigError, match="filler_words"):
        load_config(tmp_path)


def test_non_list_value_is_config_error(tmp_path: Path) -> None:
    """A value that is not a list of strings is rejected with its key."""
    _write(tmp_path, '[tool.headgate-verify]\npost-reads = "search"\n')
    with pytest.raises(ConfigError, match="post-reads"):
        load_config(tmp_path)


def test_non_string_item_is_config_error(tmp_path: Path) -> None:
    """A list holding a non-string is rejected with its key."""
    _write(tmp_path, "[tool.headgate-verify]\npost-reads = [1]\n")
    with pytest.raises(ConfigError, match="post-reads"):
        load_config(tmp_path)


def test_non_table_tool_is_config_error(tmp_path: Path) -> None:
    """A ``tool`` key that is not a table is a ConfigError, not a traceback."""
    _write(tmp_path, 'tool = "x"\n')
    with pytest.raises(ConfigError, match=r"\[tool\] must be a table"):
        load_config(tmp_path)
