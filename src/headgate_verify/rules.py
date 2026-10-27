# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""The YAML rule engine: ast-grep rules shipped as ``headgate_verify/rules/*.yml``, run over each package's modules.

A rule file keeps ast-grep's own keys, so it reads like any ast-grep rule: ``id``, ``message``, ``severity``
(``error`` or ``warning``), ``files`` (globs relative to the package root, default every module), ``rule``,
``constraints``, ``utils`` and ``transform``, plus the informational ``language`` (``python`` only) and ``note``, which
becomes the rule's ``fix``. The last four of ast-grep's keys go to ast-grep-py unchanged.

One key is this tool's own: ``skip-packages-in: <field>`` names a ``Config`` field holding package names (the name of
the directory that holds ``client.py``); the rule does not run in a package so named.

A rule that needs a project list reads a ``Config`` field through a ``{{config.<field>}}`` placeholder, which must sit
inside a single-quoted YAML string (in practice a ``regex``). Before the YAML is parsed, the placeholder is replaced by
an alternation of the field's values, each escaped, so ``'^({{config.filler_words}})$'`` matches any one filler word;
an empty field writes an alternation that matches nothing.
"""

import functools
import re
from dataclasses import dataclass, field, fields
from importlib.resources import files as resource_files
from pathlib import PurePath
from typing import TYPE_CHECKING, Any

import yaml

from headgate_verify.config import Config
from headgate_verify.exemptions import BAD_EXEMPTION
from headgate_verify.finding import Rule, Severity
from headgate_verify.parsing import LANGUAGE, PARSE_ERROR

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from ast_grep_py import Config as SgConfig

    from headgate_verify.finding import Finding
    from headgate_verify.package import Package
    from headgate_verify.parsing import Modules

RESERVED: tuple[Rule, ...] = (BAD_EXEMPTION, PARSE_ERROR)
"""The rules the engine itself reports; no rule file or check may take one's id."""

_DEFAULT_FILES = ("**/*.py",)
_SEVERITIES: dict[str, Severity] = {"error": "error", "warning": "warning"}
_REQUIRED_KEYS = frozenset({"id", "message", "severity", "rule"})
_SG_KEYS = ("rule", "constraints", "utils", "transform")
"""The keys handed to ast-grep-py as the rule's config, when present."""
_KNOWN_KEYS = _REQUIRED_KEYS | {*_SG_KEYS, "language", "note", "files", "skip-packages-in"}
_PLACEHOLDER = re.compile(r"\{\{config\.(\w+)\}\}")
_MATCH_NOTHING = r"[^\s\S]"
_CONFIG_FIELDS = frozenset(config_field.name for config_field in fields(Config))


@dataclass(frozen=True, kw_only=True)
class YamlRule(Rule):
    """One ast-grep rule loaded from a YAML file; its ``fix`` is the YAML's ``note``, whitespace folded to spaces."""

    message: str
    files: tuple[str, ...] = _DEFAULT_FILES
    config: SgConfig
    """The YAML's ``rule``/``constraints``/``utils``/``transform``, with placeholders filled from ``Config()``."""
    source: str = field(default="", repr=False, compare=False)
    """The YAML text, re-read with each run's ``Config`` when it holds a ``{{config.<field>}}`` placeholder."""
    skip_packages_in: str | None = None
    """The ``Config`` field naming the packages this rule does not run in."""

    @property
    def config_fields(self) -> tuple[str, ...]:
        """Return the ``Config`` fields the rule reads, sorted: its placeholders and its ``skip-packages-in`` field."""
        names = {str(name) for name in _PLACEHOLDER.findall(self.source)}
        if self.skip_packages_in is not None:
            names.add(self.skip_packages_in)
        return tuple(sorted(names))

    def applies_to(self, relative: PurePath) -> bool:
        """Return whether a module at ``relative`` to the package root matches one of the rule's ``files`` globs."""
        return any(relative.full_match(glob) for glob in self.files)

    def sg_config(self, config: Config) -> SgConfig:
        """Return the ast-grep config to run under ``config``: refilled only when a placeholder reads it."""
        if config == Config() or not _PLACEHOLDER.search(self.source):
            return self.config
        return _sg_config(_load(self.source, config, self.id))


def _alternation(values: Iterable[str]) -> str:
    escaped = [re.escape(value) for value in sorted(values)]
    return "|".join(escaped) if escaped else _MATCH_NOTHING


def _load(text: str, config: Config, rule_id: str) -> dict[str, Any]:
    """Return the YAML mapping in ``text``, each ``{{config.<field>}}`` placeholder filled from ``config``."""

    def replace(match: re.Match[str]) -> str:
        return _alternation(getattr(config, match.group(1))).replace("'", "''")

    data = yaml.safe_load(_PLACEHOLDER.sub(replace, text))
    if not isinstance(data, dict):
        raise _invalid(rule_id, "the YAML must be a mapping")
    return data


def _sg_config(data: dict[str, Any]) -> SgConfig:
    sg_config: SgConfig = {"rule": data["rule"]}
    for key in _SG_KEYS[1:]:
        if key in data:
            sg_config[key] = data[key]
    return sg_config


def _invalid(rule_id: str, problem: str) -> ValueError:
    return ValueError(f"rule {rule_id}: {problem}")


def rule_from_yaml(text: str, rule_id: str) -> YamlRule:
    """Build the rule in ``text``, whose ``id:`` must equal ``rule_id``; raise ``ValueError`` naming what is wrong."""
    unknown_fields = sorted(set(_PLACEHOLDER.findall(text)) - _CONFIG_FIELDS)
    if unknown_fields:
        raise _invalid(rule_id, f"placeholder names no Config field: {unknown_fields}")
    data = _load(text, Config(), rule_id)
    missing = sorted(_REQUIRED_KEYS - set(data))
    unknown = sorted(set(data) - _KNOWN_KEYS)
    if missing or unknown:
        raise _invalid(rule_id, f"missing keys {missing}, unknown keys {unknown}")
    if data["id"] != rule_id:
        raise _invalid(rule_id, f"id {data['id']!r} differs from the file name")
    if rule_id in {rule.id for rule in RESERVED}:
        raise _invalid(rule_id, "the id is reserved")
    if data.get("language", LANGUAGE) != LANGUAGE:
        raise _invalid(rule_id, f"language must be {LANGUAGE}")
    severity = _SEVERITIES.get(data["severity"])
    if severity is None:
        raise _invalid(rule_id, f"severity must be one of {sorted(_SEVERITIES)}, not {data['severity']!r}")
    globs = data.get("files", _DEFAULT_FILES)
    if not isinstance(globs, list | tuple) or not all(isinstance(glob, str) for glob in globs):
        raise _invalid(rule_id, "files must be a list of globs")
    skip_packages_in = data.get("skip-packages-in")
    if skip_packages_in is not None and skip_packages_in not in _CONFIG_FIELDS:
        raise _invalid(rule_id, f"skip-packages-in names no Config field: {skip_packages_in!r}")
    return YamlRule(
        id=rule_id,
        severity=severity,
        fix=" ".join(str(data.get("note") or "").split()),
        message=str(data["message"]),
        files=tuple(globs),
        config=_sg_config(data),
        source=text,
        skip_packages_in=skip_packages_in,
    )


@functools.cache
def load_rules() -> tuple[YamlRule, ...]:
    """Return every rule shipped in ``headgate_verify/rules/*.yml``, sorted by id."""
    directory = resource_files("headgate_verify").joinpath("rules")
    entries = sorted((entry for entry in directory.iterdir() if entry.name.endswith(".yml")), key=lambda e: e.name)
    return tuple(
        rule_from_yaml(entry.read_text(encoding="utf-8"), entry.name.removesuffix(".yml")) for entry in entries
    )


def run_rules(pkg: Package, modules: Modules, rules: Sequence[YamlRule], config: Config) -> list[Finding]:
    """Return one finding per match of each rule in each of the parsed ``modules`` of ``pkg`` its globs name."""
    findings: list[Finding] = []
    for rule in rules:
        if rule.skip_packages_in is not None and pkg.root.name in getattr(config, rule.skip_packages_in):
            continue
        sg_config = rule.sg_config(config)
        for path, root in modules.items():
            if not rule.applies_to(PurePath(path.relative_to(pkg.root))):
                continue
            findings.extend(
                rule.finding(path, match.range().start.line + 1, rule.message)
                for match in root.root().find_all(sg_config)
            )
    return findings
