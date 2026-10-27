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

if TYPE_CHECKING:
    from collections.abc import Sequence

_USAGE_ERROR = 2


def main(argv: Sequence[str] | None = None) -> int:
    """Run the verifier and return the exit code: 0 clean, 1 errors found, 2 usage error."""
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
        sys.stderr.write(f"headgate-verify: no such path: {missing[0]}\n")
        return _USAGE_ERROR
    try:
        config = load_config(Path.cwd())
    except ConfigError as error:
        sys.stderr.write(f"headgate-verify: {error}\n")
        return _USAGE_ERROR
    findings = engine.verify(args.paths, config)
    if args.format == "json":
        rows = [
            {"rule": f.rule, "path": str(f.path), "line": f.line, "message": f.message, "severity": f.severity}
            for f in findings
        ]
        sys.stdout.write(json.dumps(rows, indent=2) + "\n")
    else:
        sys.stdout.writelines(f"{finding.render()}\n" for finding in findings)
    return 1 if any(finding.severity == "error" for finding in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
