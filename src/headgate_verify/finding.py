# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""The finding a rule reports, and what every rule has: an id, a severity and how to fix what it reports."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from pathlib import Path

type Severity = Literal["error", "warning"]


@dataclass(frozen=True, slots=True)
class Finding:
    """One rule violation at a line of a file."""

    rule: str
    path: Path
    line: int
    message: str
    severity: Severity
    fix: str = field(default="", compare=False)
    """How to fix it: the YAML rule's ``note`` or the check's registered sentence; empty when the rule gives none."""

    def render(self) -> str:
        """Return the one-line text form, ``<file>:<line> <severity> <rule> <message>``."""
        return f"{self.path}:{self.line} {self.severity} {self.rule} {self.message}"

    def to_json(self) -> dict[str, str | int]:
        """Return the JSON object form: ``rule``, ``path``, ``line``, ``message``, ``severity`` and ``fix``."""
        return {
            "rule": self.rule,
            "path": str(self.path),
            "line": self.line,
            "message": self.message,
            "severity": self.severity,
            "fix": self.fix,
        }

    def __lt__(self, other: Finding) -> bool:
        """Order by path, then line, then rule."""
        return (self.path, self.line, self.rule) < (other.path, other.line, other.rule)


@dataclass(frozen=True, kw_only=True)
class Rule:
    """A rule the verifier reports under: a YAML rule, a Python check, or one the engine itself reports.

    Its id is the name allow comments use and its fixture directory ``tests/rules/<id>/`` takes.
    """

    id: str
    severity: Severity
    fix: str = ""
    """How to fix a finding of this rule, printed under it; empty when the rule gives none."""

    def finding(self, path: Path, line: int, message: str) -> Finding:
        """Return a finding of this rule at ``path``:``line``, carrying the rule's severity and fix."""
        return Finding(self.id, path, line, message, self.severity, self.fix)
