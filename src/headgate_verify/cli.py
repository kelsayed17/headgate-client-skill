# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""The ``headgate-verify`` command."""

import argparse
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from headgate_verify import engine
from headgate_verify.config import ConfigError, load_config
from headgate_verify.package import NoPackageError, find_packages

if TYPE_CHECKING:
    from collections.abc import Sequence

    from headgate_verify.finding import Finding

_USAGE_ERROR = 2
_FIX_INDENT = "    "


def main(argv: Sequence[str] | None = None) -> int:
    """Run the verifier and return the exit code: 0 clean, 1 errors found, 2 usage error.

    stdout carries only the findings; stderr carries usage errors and, after a run, ``checked N package(s)``.
    """
    parser = argparse.ArgumentParser(prog="headgate-verify", description="Check headgate API clients.")
    parser.add_argument("paths", nargs="*", type=Path, help="client packages or directories containing them")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exit_:
        return int(exit_.code or 0) if isinstance(exit_.code, int) else _USAGE_ERROR
    if not args.paths:
        parser.print_usage(sys.stderr)
        return _USAGE_ERROR
    missing = [path for path in args.paths if not path.exists()]
    if missing:
        sys.stderr.writelines(f"headgate-verify: no such path: {path}\n" for path in missing)
        return _USAGE_ERROR
    try:
        config = load_config(Path.cwd())
    except ConfigError as error:
        sys.stderr.write(f"headgate-verify: {error}\n")
        return _USAGE_ERROR
    try:
        packages = find_packages(args.paths)
    except NoPackageError as error:
        sys.stderr.writelines(
            f"headgate-verify: no client package (a directory holding client.py) under {path}\n" for path in error.paths
        )
        return _USAGE_ERROR
    findings = engine.verify_packages(packages, config)
    if args.format == "json":
        sys.stdout.write(json.dumps([finding.to_json() for finding in findings], indent=2) + "\n")
    else:
        sys.stdout.writelines(_text(finding) for finding in findings)
    sys.stderr.write(f"checked {len(packages)} package(s)\n")
    return 1 if any(finding.severity == "error" for finding in findings) else 0


def _text(finding: Finding) -> str:
    """Return the finding's line, then its fix indented on the next line when it has one."""
    return f"{finding.render()}\n" + (f"{_FIX_INDENT}{finding.fix}\n" if finding.fix else "")


if __name__ == "__main__":
    raise SystemExit(main())
