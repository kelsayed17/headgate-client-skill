# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""The YAML rule engine: ast-grep rules shipped as ``headgate_verify/rules/*.yml``, run over each package's modules.

A rule file keeps ast-grep's own keys, so it reads like any ast-grep rule: ``id``, ``message``, ``severity``
(``error`` or ``warning``), ``files`` (globs relative to the package root, default every module), ``rule``,
``constraints``, ``utils`` and ``transform``, plus the informational ``language`` (``python`` only) and ``note``.
The last four of ast-grep's keys go to ast-grep-py unchanged.

A rule that needs a project list reads a ``Config`` field through a ``{{config.<field>}}`` placeholder, which must sit
inside a single-quoted YAML string (in practice a ``regex``). Before the YAML is parsed, the placeholder is replaced by
an alternation of the field's values, each escaped, so ``'^({{config.filler_words}})$'`` matches any one filler word;
an empty field writes an alternation that matches nothing.
"""

import functools
import re
from dataclasses import dataclass, field, fields
from importlib.resources import files as resource_files
from pathlib import Path, PurePath
from typing import TYPE_CHECKING

import yaml
from ast_grep_py import Config as SgConfig
from ast_grep_py import SgRoot

from headgate_verify.config import Config
from headgate_verify.finding import Finding, Severity

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from headgate_verify.package import Package

PARSE_ERROR = "parse-error"
"""The reserved id of the finding for a module that does not parse."""
BAD_EXEMPTION = "bad-exemption"
"""The reserved id of the finding for a malformed, unknown or unused allow comment."""
RESERVED_RULES = (BAD_EXEMPTION, PARSE_ERROR)
"""Rule ids the engine itself reports; no rule file or check may take one."""

_LANGUAGE = "python"
_DEFAULT_FILES = ("**/*.py",)
_SEVERITIES: dict[str, Severity] = {"error": "error", "warning": "warning"}
_REQUIRED_KEYS = frozenset({"id", "message", "severity", "rule"})
_KNOWN_KEYS = _REQUIRED_KEYS | {"language", "note", "files", "constraints", "utils", "transform"}
_PLACEHOLDER = re.compile(r"\{\{config\.(\w+)\}\}")
_MATCH_NOTHING = r"[^\s\S]"


@dataclass(frozen=True)
class YamlRule:
    """One ast-grep rule loaded from a YAML file."""

    id: str
    message: str
    severity: Severity
    files: tuple[str, ...]
    config: SgConfig
    """The YAML's ``rule``/``constraints``/``utils``/``transform``, with placeholders filled from ``Config()``."""
    source: str = field(default="", repr=False, compare=False)
    """The YAML text, re-read with each run's ``Config`` when it holds a ``{{config.<field>}}`` placeholder."""

    def applies_to(self, relative: PurePath) -> bool:
        """Return whether a module at ``relative`` to the package root matches one of the rule's ``files`` globs."""
        return any(relative.full_match(glob) for glob in self.files)


def _alternation(values: Iterable[str]) -> str:
    escaped = [re.escape(value) for value in sorted(values)]
    return "|".join(escaped) if escaped else _MATCH_NOTHING


def _fill(text: str, config: Config) -> str:
    def replace(match: re.Match[str]) -> str:
        return _alternation(getattr(config, match.group(1))).replace("'", "''")

    return _PLACEHOLDER.sub(replace, text)


def _sg_config(text: str, config: Config) -> SgConfig:
    data = yaml.safe_load(_fill(text, config))
    sg_config: SgConfig = {"rule": data["rule"]}
    if "constraints" in data:
        sg_config["constraints"] = data["constraints"]
    if "utils" in data:
        sg_config["utils"] = data["utils"]
    if "transform" in data:
        sg_config["transform"] = data["transform"]
    return sg_config


def rule_from_yaml(text: str, rule_id: str) -> YamlRule:
    """Build the rule in ``text``, whose ``id:`` must equal ``rule_id``; raise ``ValueError`` naming what is wrong."""
    config_fields = {config_field.name for config_field in fields(Config)}
    unknown_fields = sorted(set(_PLACEHOLDER.findall(text)) - config_fields)
    if unknown_fields:
        msg = f"rule {rule_id}: placeholder names no Config field: {unknown_fields}"
        raise ValueError(msg)
    data = yaml.safe_load(_fill(text, Config()))
    if not isinstance(data, dict):
        msg = f"rule {rule_id}: the YAML must be a mapping"
        raise ValueError(msg)  # noqa: TRY004 - a malformed rule file is a value error, like every other refusal here
    missing = sorted(_REQUIRED_KEYS - set(data))
    unknown = sorted(set(data) - _KNOWN_KEYS)
    if missing or unknown:
        msg = f"rule {rule_id}: missing keys {missing}, unknown keys {unknown}"
        raise ValueError(msg)
    if data["id"] != rule_id:
        msg = f"rule {rule_id}: id {data['id']!r} differs from the file name"
        raise ValueError(msg)
    if rule_id in RESERVED_RULES:
        msg = f"rule {rule_id}: the id is reserved"
        raise ValueError(msg)
    if data.get("language", _LANGUAGE) != _LANGUAGE:
        msg = f"rule {rule_id}: language must be {_LANGUAGE}"
        raise ValueError(msg)
    severity = _SEVERITIES.get(data["severity"])
    if severity is None:
        msg = f"rule {rule_id}: severity must be one of {sorted(_SEVERITIES)}, not {data['severity']!r}"
        raise ValueError(msg)
    globs = data.get("files", _DEFAULT_FILES)
    if not isinstance(globs, list | tuple) or not all(isinstance(glob, str) for glob in globs):
        msg = f"rule {rule_id}: files must be a list of globs"
        raise ValueError(msg)
    return YamlRule(
        id=rule_id,
        message=str(data["message"]),
        severity=severity,
        files=tuple(globs),
        config=_sg_config(text, Config()),
        source=text,
    )


@functools.cache
def load_rules() -> tuple[YamlRule, ...]:
    """Return every rule shipped in ``headgate_verify/rules/*.yml``, sorted by id."""
    directory = resource_files("headgate_verify").joinpath("rules")
    entries = sorted((entry for entry in directory.iterdir() if entry.name.endswith(".yml")), key=lambda e: e.name)
    return tuple(
        rule_from_yaml(entry.read_text(encoding="utf-8"), entry.name.removesuffix(".yml")) for entry in entries
    )


@dataclass(frozen=True)
class _Parsed:
    roots: dict[Path, SgRoot]
    errors: tuple[Finding, ...]


def _parse_error(path: Path, line: int, detail: str) -> Finding:
    return Finding(PARSE_ERROR, path, line, f"the module does not parse ({detail}); no other rule read it", "error")


@functools.cache
def _parsed(pkg: Package) -> _Parsed:
    roots: dict[Path, SgRoot] = {}
    errors: list[Finding] = []
    for path in pkg.modules:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as error:
            errors.append(_parse_error(path, 1, f"not UTF-8: {error.reason}"))
            continue
        root = SgRoot(text, _LANGUAGE)
        broken = root.root().find(kind="ERROR")
        if broken is None:
            roots[path] = root
        else:
            errors.append(_parse_error(path, broken.range().start.line + 1, "syntax error"))
    return _Parsed(roots, tuple(errors))


def parse(pkg: Package) -> dict[Path, SgRoot]:
    """Return each module of ``pkg`` that parses, with its tree; parsed once per run (see ``clear_cache``)."""
    return _parsed(pkg).roots


def parse_errors(pkg: Package) -> list[Finding]:
    """Return a ``parse-error`` finding for each module of ``pkg`` that does not parse."""
    return list(_parsed(pkg).errors)


def clear_cache() -> None:
    """Forget every parsed package, so the next run re-reads the files."""
    _parsed.cache_clear()


def _effective_config(rule: YamlRule, config: Config) -> SgConfig:
    if config == Config() or not _PLACEHOLDER.search(rule.source):
        return rule.config
    return _sg_config(rule.source, config)


def run_rules(pkg: Package, rules: Sequence[YamlRule], config: Config) -> list[Finding]:
    """Return one finding per match of each rule in each module of ``pkg`` its ``files`` globs name."""
    findings: list[Finding] = []
    modules = parse(pkg)
    for rule in rules:
        sg_config = _effective_config(rule, config)
        for path, root in modules.items():
            if not rule.applies_to(PurePath(path.relative_to(pkg.root))):
                continue
            findings.extend(
                Finding(rule.id, path, match.range().start.line + 1, rule.message, rule.severity)
                for match in root.root().find_all(sg_config)
            )
    return findings
