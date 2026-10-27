# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""Run every check over the client packages under the given paths."""

from typing import TYPE_CHECKING

from headgate_verify.config import Config
from headgate_verify.package import Package, find_packages

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from headgate_verify.finding import Finding


def verify(paths: Sequence[Path], config: Config | None = None) -> list[Finding]:
    """Return the sorted findings for every package under ``paths``."""
    config = config or Config()
    findings: list[Finding] = []
    for package in find_packages(paths):
        findings.extend(_check(package, config))
    return sorted(findings)


def _check(package: Package, config: Config) -> list[Finding]:  # noqa: ARG001
    """Run the registered checks over one package; none are registered yet."""
    return []
