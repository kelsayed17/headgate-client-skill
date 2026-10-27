# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""Allow comments: ``# headgate-verify: allow <rule-id> -- <reason>``.

A finding is dropped when its own line, or the ``def``/``class`` line of any function or class enclosing it, carries
an allow comment naming its rule with a reason. A finding against the whole module (a match of the ``module`` node,
reported at the module's first line) is also covered by an allow comment anywhere before the module's first statement,
so it can sit below a license header. Every ``# headgate-verify:`` comment that is malformed, gives no
reason, names an unknown rule, or drops no finding is itself an error, ``bad-exemption``.
"""

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from headgate_verify.finding import Finding
from headgate_verify.rules import BAD_EXEMPTION

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from ast_grep_py import SgRoot

_DIRECTIVE = re.compile(r"#\s*headgate-verify:")
_ALLOW = re.compile(r"#\s*headgate-verify:\s*allow\s+(?P<rule>[\w.-]+)(?:\s+--(?P<reason>.*))?\s*")
_FORM = "`# headgate-verify: allow <rule-id> -- <reason>`"


@dataclass(frozen=True)
class _Allow:
    line: int
    rule: str


def _bad(path: Path, line: int, message: str) -> Finding:
    return Finding(BAD_EXEMPTION, path, line, message, "error")


def _allows(path: Path, root: SgRoot, known: frozenset[str]) -> tuple[list[_Allow], list[Finding]]:
    allows: list[_Allow] = []
    bad: list[Finding] = []
    for comment in root.root().find_all(kind="comment"):
        text = comment.text()
        if not _DIRECTIVE.match(text):
            continue
        line = comment.range().start.line + 1
        allow = _ALLOW.fullmatch(text)
        if allow is None:
            bad.append(_bad(path, line, f"malformed headgate-verify comment; expected {_FORM}"))
        elif not (allow["reason"] or "").strip():
            bad.append(_bad(path, line, f"allow comment for {allow['rule']} gives no reason after `--`"))
        elif allow["rule"] not in known:
            bad.append(_bad(path, line, f"allow comment names unknown rule {allow['rule']}"))
        else:
            allows.append(_Allow(line, allow["rule"]))
    return allows, bad


def _scope_lines(root: SgRoot) -> list[tuple[int, int]]:
    """Return ``(def/class line, last line)`` for every function and class, 1-based."""
    scopes = root.root().find_all(any=[{"kind": "function_definition"}, {"kind": "class_definition"}])
    return [(node.range().start.line + 1, node.range().end.line + 1) for node in scopes]


def _leading_lines(root: SgRoot) -> set[int]:
    """Return the module's first line and every line before its first statement, 1-based."""
    module = root.root()
    first = module.range().start.line + 1
    statements = [child for child in module.children() if child.is_named() and child.kind() != "comment"]
    end = statements[0].range().start.line + 1 if statements else module.range().end.line + 2
    return {first} | set(range(first, end))


def apply_exemptions(
    findings: Iterable[Finding], modules: dict[Path, SgRoot], known_rules: frozenset[str]
) -> list[Finding]:
    """Return ``findings`` without the ones an allow comment covers, plus a ``bad-exemption`` per bad comment.

    ``modules`` are the parsed modules whose comments are read; a finding in any other file is kept as it is.
    ``known_rules`` are the ids an allow comment may name.
    """
    kept: list[Finding] = []
    by_path: dict[Path, list[Finding]] = {}
    for finding in findings:
        (by_path.setdefault(finding.path, []) if finding.path in modules else kept).append(finding)
    for path, root in modules.items():
        allows, bad = _allows(path, root, known_rules)
        kept.extend(bad)
        scopes = _scope_lines(root)
        module_line = root.root().range().start.line + 1
        leading = _leading_lines(root)
        used: set[_Allow] = set()
        for finding in by_path.get(path, []):
            lines = {finding.line} | {start for start, end in scopes if start <= finding.line <= end}
            if finding.line == module_line:
                lines |= leading
            covering = [allow for allow in allows if allow.rule == finding.rule and allow.line in lines]
            if covering:
                used.update(covering)
            else:
                kept.append(finding)
        kept.extend(
            _bad(path, allow.line, f"allow comment for {allow.rule} suppresses nothing")
            for allow in allows
            if allow not in used
        )
    return kept
