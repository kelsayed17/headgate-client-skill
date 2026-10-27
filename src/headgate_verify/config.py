# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""Verifier configuration, read from ``[tool.headgate-verify]`` in the nearest ``pyproject.toml``."""

import tomllib
from dataclasses import dataclass, fields
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


class ConfigError(ValueError):
    """The ``[tool.headgate-verify]`` table is malformed; the message names the offending key."""


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


def load_config(start: Path) -> Config:
    """Return the config from the nearest ``pyproject.toml`` at or above ``start``; defaults if none or no table."""
    start = start.resolve()
    for directory in (start, *start.parents):
        pyproject = directory / "pyproject.toml"
        if pyproject.is_file():
            return _from_file(pyproject)
    return Config()


def _from_file(pyproject: Path) -> Config:
    try:
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as error:
        msg = f"{pyproject}: not valid TOML: {error}"
        raise ConfigError(msg) from error
    table = data.get("tool", {}).get("headgate-verify", {})
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
