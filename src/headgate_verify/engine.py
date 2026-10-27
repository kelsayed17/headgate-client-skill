# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""Run every rule and check over the client packages under the given paths."""

from typing import TYPE_CHECKING

from headgate_verify import rules
from headgate_verify.checks import CHECKS
from headgate_verify.config import Config
from headgate_verify.exemptions import apply_exemptions
from headgate_verify.package import Package, find_packages

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from headgate_verify.finding import Finding


def verify(paths: Sequence[Path], config: Config | None = None) -> list[Finding]:
    """Return the sorted findings for every package under ``paths``; ``Config()`` when ``config`` is None."""
    config = Config() if config is None else config
    yaml_rules = rules.load_rules()
    known = frozenset(rule.id for rule in yaml_rules) | {name for name, _ in CHECKS}
    rules.clear_cache()
    findings: list[Finding] = []
    for package in find_packages(paths):
        findings.extend(_check(package, yaml_rules, known, config))
    rules.clear_cache()
    return sorted(findings)


def _check(
    package: Package, yaml_rules: Sequence[rules.YamlRule], known: frozenset[str], config: Config
) -> list[Finding]:
    """Run the YAML rules and the Python checks over one package, then apply its allow comments."""
    modules = rules.parse(package)
    raw = rules.run_rules(package, yaml_rules, config)
    for _, check in CHECKS:
        raw.extend(check(package, modules, config))
    return [*rules.parse_errors(package), *apply_exemptions(raw, modules, known)]
