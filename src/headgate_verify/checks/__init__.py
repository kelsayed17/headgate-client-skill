# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""Checks written in Python over the ast-grep-py trees, for rules a YAML pattern cannot express.

A check takes the package, its parsed modules (``rules.parse``: unparseable modules are left out, and reported as
``parse-error`` by the engine) and the ``Config``, and returns its findings. ``CHECKS`` registers each check under
its rule id, which is also the name its allow comments and its fixture directory ``tests/rules/<id>/`` use.
"""

from collections.abc import Callable
from typing import TYPE_CHECKING

from headgate_verify.checks import flavour, hosts, layout, models, warnings

if TYPE_CHECKING:
    from pathlib import Path

    from ast_grep_py import SgRoot

    from headgate_verify.config import Config
    from headgate_verify.finding import Finding
    from headgate_verify.package import Package

type Check = Callable[[Package, dict[Path, SgRoot], Config], list[Finding]]


CHECKS: tuple[tuple[str, Check], ...] = (
    (hosts.RULE, hosts.check),
    (models.RULE, models.check),
    (layout.RULE, layout.check),
    (flavour.RULE, flavour.check),
    (warnings.EXCEPT_RULE, warnings.check_except),
    (warnings.CACHE_RULE, warnings.check_cache),
)
"""Every Python check, as ``(rule id, check)``."""
