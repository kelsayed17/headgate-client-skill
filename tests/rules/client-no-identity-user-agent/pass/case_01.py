# Copyright line
# second comment
"""AcmeClient/1.0 is refused."""

from __future__ import annotations


class Feed:
    """AcmeClient/1.0 for example."""

    def read(self) -> None:
        """AcmeClient/1.0 is sent."""


async def fetch() -> None:
    """AcmeClient/1.0"""


def joined() -> None:
    "AcmeClient/1.0 " "second half"


def wrapped() -> None:
    ("AcmeClient/1.0")


def double() -> None:
    (("AcmeClient/1.0"))
