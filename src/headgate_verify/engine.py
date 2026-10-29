# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""Run every rule and check over client packages: parse each package once, run the rules, then the allow comments."""

from typing import TYPE_CHECKING

from headgate_verify.checks import CHECKS
from headgate_verify.config import Config
from headgate_verify.exemptions import apply_exemptions
from headgate_verify.package import find_packages
from headgate_verify.parsing import parse_package
from headgate_verify.rules import RESERVED, load_project_rules, load_rules, run_rules

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from headgate_verify.finding import Finding, Rule
    from headgate_verify.package import Package
    from headgate_verify.rules import YamlRule


def all_rules(config: Config | None = None) -> tuple[Rule, ...]:
    """Return every rule a finding can be reported under: the YAML rules, the Python checks, the engine's own.

    With a ``config``, the project's rules from its ``rule-dirs`` are among them.
    """
    return (*yaml_rules(config), *(check.rule for check in CHECKS), *RESERVED)


def yaml_rules(config: Config | None = None) -> tuple[YamlRule, ...]:
    """Return the shipped YAML rules, then the project's from ``config.rule_dirs``; raise ``ValueError`` on a clash.

    A project rule may not take a Python check's id either, so an allow comment names exactly one rule.
    """
    project = load_project_rules(config.rule_dirs) if config is not None else ()
    clashes = sorted({rule.id for rule in project} & {check.rule.id for check in CHECKS})
    if clashes:
        msg = f"project rules take the ids of checks: {clashes}"
        raise ValueError(msg)
    return (*load_rules(), *project)


def verify(paths: Sequence[Path], config: Config | None = None) -> list[Finding]:
    """Return the sorted findings for every package under ``paths``; ``Config()`` when ``config`` is None.

    Raise ``NoPackageError`` (from ``find_packages``) naming every path under which no client package is found.
    """
    return verify_packages(find_packages(paths), config)


def verify_packages(packages: Sequence[Package], config: Config | None = None) -> list[Finding]:
    """Return the sorted findings for ``packages``; ``Config()`` when ``config`` is None.

    Each finding carries its rule's fix: a YAML rule's ``note``, a check's or the engine's registered sentence.
    """
    config = Config() if config is None else config
    rules = yaml_rules(config)
    known = frozenset(rule.id for rule in all_rules(config))
    findings: list[Finding] = []
    for package in packages:
        parsed = parse_package(package)
        raw = run_rules(package, parsed.modules, rules, config)
        for check in CHECKS:
            raw.extend(check.run(package, parsed.modules, config))
        findings.extend(parsed.errors)
        findings.extend(apply_exemptions(raw, parsed.modules, known))
    return sorted(findings)
