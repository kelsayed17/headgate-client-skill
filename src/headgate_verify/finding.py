# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""The finding a check reports."""

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

    def __lt__(self, other: Finding) -> bool:
        """Order by path, then line, then rule."""
        return (self.path, self.line, self.rule) < (other.path, other.line, other.rule)
