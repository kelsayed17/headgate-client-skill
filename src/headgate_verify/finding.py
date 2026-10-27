# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""The finding a check reports."""

from dataclasses import dataclass
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

    def render(self) -> str:
        """Return the one-line text form."""
        return f"{self.path}:{self.line} {self.rule} {self.message}"

    def __lt__(self, other: Finding) -> bool:
        """Order by path, then line, then rule."""
        return (self.path, self.line, self.rule) < (other.path, other.line, other.rule)
