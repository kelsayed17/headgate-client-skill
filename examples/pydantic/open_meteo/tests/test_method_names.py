# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""The clients' method names follow the documented paths saved in ``docs_paths.json``."""

from pathlib import Path

from headgate_verify.naming import check_names

PACKAGE = Path(__file__).parent.parent


def test_method_names_follow_the_docs() -> None:
    """Each documented read has one method, named after its path, and every method's path is documented.

    Both classes of ``client.py`` are read: ``ForecastClient.get_forecast`` reads ``/v1/forecast`` and
    ``ArchiveClient.get_archive`` reads ``/v1/archive``, each on its own host. No overrides: each name is the one its
    path derives (``v1`` is dropped).
    """
    assert check_names(PACKAGE / "client.py", PACKAGE / "docs_paths.json") == []
