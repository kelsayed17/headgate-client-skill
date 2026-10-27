# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""The client's method names follow the documented paths saved in ``docs_paths.json``."""

from pathlib import Path

from headgate_verify.naming import check_names

PACKAGE = Path(__file__).parent.parent


def test_method_names_follow_the_docs() -> None:
    """Every documented read has one method, named after its path, and every method's path is documented.

    No overrides: every name is the one the path derives (``api`` and ``v1`` are dropped; an item endpoint singularises
    because its list shares the name).
    """
    assert check_names(PACKAGE / "client.py", PACKAGE / "docs_paths.json") == []
