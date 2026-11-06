# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""The pytest options that name a suite's credentials provider (:mod:`headgate_verify.testing.creds`).

Not registered as a ``pytest11`` entry point, so installing ``headgate-verify`` changes no other suite. A client's
top-level ``conftest.py`` opts in::

    pytest_plugins = ["headgate_verify.testing.plugin"]

Then ``pytest --credentials-provider mypkg.secrets:lookup`` (or ``credentials_provider = "mypkg.secrets:lookup"`` in
the ini) installs ``lookup`` before collection; with neither, every live test that needs a credential skips.
"""

from typing import TYPE_CHECKING

from headgate_verify.testing import creds

if TYPE_CHECKING:
    import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add ``--credentials-provider module:function`` and its ini twin."""
    parser.addoption(
        "--credentials-provider",
        default=None,
        help="module:function answering (provider, field) with a credential or None (headgate_verify.testing.creds)",
    )
    parser.addini("credentials_provider", "the same as --credentials-provider, for an ini file", default="")


def pytest_configure(config: pytest.Config) -> None:
    """Install the named credentials provider, or none."""
    spec = config.getoption("--credentials-provider") or config.getini("credentials_provider")
    creds.use(creds.load_provider(spec) if spec else None)
