# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""A warning, for what a pattern can find but only a reader can judge. A warning never fails the run (exit 0).

``client-except-needs-review``: every ``except`` clause of every module of the package is reported, at the clause's
line, once per clause. A client's errors are ``headgate.errors`` types the caller handles; a handler that turns one
into a return value, or into another exception type, changes what the caller sees. The finding asks the agent to
confirm the handler re-raises a ``headgate.errors`` type, or that the swallowed error is a documented answer, and to
record which with an allow comment carrying the reason. ``try``/``finally`` with no handler is not reported.

DISCLOSED: ``except`` clauses in a module the parser cannot read are not seen (the engine reports that module as
``parse-error``).
"""

from typing import TYPE_CHECKING

from headgate_verify.finding import Rule
from headgate_verify.syntax import line

if TYPE_CHECKING:
    from headgate_verify.config import Config
    from headgate_verify.finding import Finding
    from headgate_verify.package import Package
    from headgate_verify.parsing import Modules

RULE = Rule(
    id="client-except-needs-review",
    severity="warning",
    fix="Make the handler re-raise a `headgate.errors` type, or confirm the swallowed error is a documented answer, "
    "and record which with an allow comment carrying the reason.",
)


def check(pkg: Package, modules: Modules, config: Config) -> list[Finding]:
    """Return a warning for each ``except`` clause in the package."""
    del config
    return [
        RULE.finding(
            path,
            line(clause),
            "this handler must re-raise a headgate.errors type, or the error must be a documented answer of the "
            "provider; confirm which, and record the reason with an allow comment",
        )
        for path in pkg.modules
        if (root := modules.get(path)) is not None
        for clause in root.root().find_all(kind="except_clause")
    ]
