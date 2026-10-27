# Copyright line
# second comment
"""Mozilla/5.0 is refused."""

from __future__ import annotations


class Feed:
    """Mozilla/5.0 for example."""

    def read(self) -> None:
        """Mozilla/5.0 is sent."""


async def fetch() -> None:
    """Mozilla/5.0"""


def joined() -> None:
    "Mozilla/5.0 " "second half"


def wrapped() -> None:
    ("Mozilla/5.0")


def double() -> None:
    (("Mozilla/5.0"))
