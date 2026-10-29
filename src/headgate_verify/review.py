# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""The ``headgate-names`` command: list the method names the naming rules cannot produce well, for review.

``headgate-names <package>/tests/test_method_names.py`` runs the test module's top level (not its tests) and reads
the tables it passes to ``check_names``: ``PACKAGE`` (the directory holding ``client.py`` and ``docs_paths.json``),
and ``OVERRIDES``, ``EXEMPT_WRITES``, ``POST_READS`` and ``FILLER`` when it defines them. It prints one line per
``review_names`` sentence and exits 0: the list is for a person or an agent to judge, never a failure.
"""

import argparse
import runpy
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from headgate_verify.config import ConfigError
from headgate_verify.naming import review_names
from headgate_verify.snapshot import SnapshotError

if TYPE_CHECKING:
    from collections.abc import Sequence

_USAGE_ERROR = 2


def main(argv: Sequence[str] | None = None) -> int:
    """Print the review list of the package the test module names; return 0, or 2 when it cannot be read."""
    parser = argparse.ArgumentParser(prog="headgate-names", description="List method names to review.")
    parser.add_argument("test_module", type=Path, help="the package's test_method_names.py")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exit_:
        return int(exit_.code or 0) if isinstance(exit_.code, int) else _USAGE_ERROR
    test_module = Path(args.test_module)
    try:
        tables = runpy.run_path(str(test_module))
    except (OSError, SyntaxError, ImportError) as error:
        sys.stderr.write(f"headgate-names: {test_module} cannot be run: {error}\n")
        return _USAGE_ERROR
    package = tables.get("PACKAGE")
    if not isinstance(package, Path):
        sys.stderr.write(f"headgate-names: {test_module} defines no PACKAGE path (the directory of client.py)\n")
        return _USAGE_ERROR
    try:
        review = review_names(
            package / "client.py",
            package / "docs_paths.json",
            overrides=tables.get("OVERRIDES", {}),
            exempt_writes=tables.get("EXEMPT_WRITES", ()),
            post_reads=tables.get("POST_READS"),
            filler=tables.get("FILLER"),
        )
    except (SnapshotError, ConfigError, OSError) as error:
        sys.stderr.write(f"headgate-names: {error}\n")
        return _USAGE_ERROR
    sys.stdout.writelines(f"{line}\n" for line in review)
    sys.stderr.write(f"{len(review)} name(s) to review\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
