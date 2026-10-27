# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""Verifier configuration, read from ``[tool.headgate-verify]`` in the nearest ``pyproject.toml``.

``read_pyproject`` is the one reader of a ``pyproject.toml``: the config and the ``one-flavour`` check both use it.
"""

import tomllib
from dataclasses import dataclass, fields
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path


class PyprojectError(ValueError):
    """A ``pyproject.toml`` cannot be read, is not UTF-8 or is not valid TOML; the message names the file and why."""


class ConfigError(ValueError):
    """The ``pyproject.toml`` holding the config cannot be read, or its table is malformed; the message says how."""


@dataclass(frozen=True)
class Config:
    """Settings that tune the checks."""

    browser_user_agent_packages: frozenset[str] = frozenset()
    """Package names allowed a browser-spoofing User-Agent."""
    filler_words: frozenset[str] = frozenset({"api", "locale", "us", "global", "markets", "market"})
    """Words ignored when comparing names."""
    post_reads: frozenset[str] = frozenset()
    """Method names that read by POST."""
    write_name_fragments: frozenset[str] = frozenset({"order", "orders", "transfer", "withdraw", "payment"})
    """Name fragments that mark a method as a write."""


def nearest_pyproject(start: Path) -> Path | None:
    """Return the nearest ``pyproject.toml`` at or above ``start``, or None."""
    start = start.resolve()
    for directory in (start, *start.parents):
        pyproject = directory / "pyproject.toml"
        if pyproject.is_file():
            return pyproject
    return None


def read_pyproject(pyproject: Path) -> dict[str, Any]:
    """Return the TOML in ``pyproject``; raise ``PyprojectError`` when it cannot be read, is not UTF-8 or not TOML."""
    try:
        text = pyproject.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        msg = f"{pyproject} is not UTF-8 ({error.reason})"
        raise PyprojectError(msg) from error
    except OSError as error:
        msg = f"{pyproject} cannot be read ({error.strerror or error})"
        raise PyprojectError(msg) from error
    try:
        return tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        msg = f"{pyproject} is not valid TOML ({error})"
        raise PyprojectError(msg) from error


def load_config(start: Path) -> Config:
    """Return the config from the nearest ``pyproject.toml`` at or above ``start``; defaults if none or no table."""
    pyproject = nearest_pyproject(start)
    return Config() if pyproject is None else _from_file(pyproject)


def _from_file(pyproject: Path) -> Config:
    try:
        data = read_pyproject(pyproject)
    except PyprojectError as error:
        raise ConfigError(str(error)) from error
    tool = data.get("tool", {})
    if not isinstance(tool, dict):
        msg = f"{pyproject}: [tool] must be a table"
        raise ConfigError(msg)
    table = tool.get("headgate-verify", {})
    if not isinstance(table, dict):
        msg = f"{pyproject}: [tool.headgate-verify] must be a table"
        raise ConfigError(msg)
    known = {f.name.replace("_", "-"): f.name for f in fields(Config)}
    values: dict[str, frozenset[str]] = {}
    for key, value in table.items():
        if key not in known:
            msg = f"{pyproject}: unknown key {key!r} in [tool.headgate-verify]; expected one of {sorted(known)}"
            raise ConfigError(msg)
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            msg = f"{pyproject}: {key!r} in [tool.headgate-verify] must be a list of strings"
            raise ConfigError(msg)
        values[known[key]] = frozenset(value)
    return Config(**values)
