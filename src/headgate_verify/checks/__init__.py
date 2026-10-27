# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""Checks written in Python over the ast-grep-py trees, for rules a YAML pattern cannot express.

Each check module defines its ``RULE`` (id, severity and fix sentence) and a ``check`` that takes the package, its
parsed modules (unparseable modules are left out, and reported as ``parse-error`` by the engine) and the ``Config``,
and returns the findings it builds with ``RULE.finding``. ``CHECKS`` registers each pair. The id is also the name its
allow comments and its fixture directory ``tests/rules/<id>/`` use, and its module docstring opens its description
with ``<id>``: and the sentence the generated rule list shows.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from headgate_verify.checks import caching, flavour, handlers, hosts, layout, models

if TYPE_CHECKING:
    from headgate_verify.config import Config
    from headgate_verify.finding import Finding, Rule
    from headgate_verify.package import Package
    from headgate_verify.parsing import Modules

type CheckFunction = Callable[[Package, Modules, Config], list[Finding]]


@dataclass(frozen=True)
class Check:
    """A Python check: the rule its findings are reported under, and the function that finds them."""

    rule: Rule
    run: CheckFunction


CHECKS: tuple[Check, ...] = (
    Check(hosts.RULE, hosts.check),
    Check(models.RULE, models.check),
    Check(layout.RULE, layout.check),
    Check(flavour.RULE, flavour.check),
    Check(handlers.RULE, handlers.check),
    Check(caching.RULE, caching.check),
)
"""Every Python check, in the order the engine runs them."""
