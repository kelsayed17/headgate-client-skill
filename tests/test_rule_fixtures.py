# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""The fixture harness: every rule proves itself on the fixtures under ``tests/rules/<rule-id>/``.

Conventions, for whoever adds a rule or a check:

* One directory per rule id, ``tests/rules/<rule-id>/``, with a ``fail/`` and a ``pass/`` directory. The id is the
  YAML rule's file stem, the name a Python check registers in ``CHECKS``, or a reserved id (``parse-error``,
  ``bad-exemption``). ``test_every_rule_has_fixtures`` fails for a rule with no ``fail`` or no ``pass`` entry, and
  for a fixture directory that names no rule.
* Every entry in ``fail/`` must yield at least one finding whose ``rule`` is the directory's id; every entry in
  ``pass/`` must yield none with that id. Findings of other rules are ignored, so a fixture needs to be clean only
  for its own rule.
* An entry is either a ``.py`` file or a directory. A ``.py`` file is copied into a fresh temporary package as its
  ``client.py``. A directory is copied whole and is the package, so it must hold a ``client.py``; use one when the
  rule reads more than one module or a ``pyproject.toml``. A directory may instead hold one subdirectory holding the
  ``client.py`` (``params_and_body/widgets/client.py``): that subdirectory is the package, under its own name, for a
  rule that reads the package's name. Both are copied out of the repository first, so no ``pyproject.toml`` of this
  repository is ever the nearest one.
* A fixture sets ``Config`` fields with a JSON object on line 1 of its ``.py`` file (of ``client.py`` for a
  directory), each value a list of strings::

      # headgate-verify-config: {"filler_words": ["api", "v2"]}

* Fixtures under ``tests/rules/`` are not linted, formatted or type-checked, and pytest does not collect them.
* A finding is exempted by a comment on its line, or on the ``def``/``class`` line enclosing it::

      # headgate-verify: allow <rule-id> -- <reason>

  An allow comment with no reason after ``--``, naming an unknown rule, or suppressing nothing, is itself a
  ``bad-exemption`` error.
"""

import json
import shutil
from dataclasses import fields
from pathlib import Path

import pytest

from headgate_verify.checks import CHECKS
from headgate_verify.config import Config
from headgate_verify.engine import verify
from headgate_verify.rules import RESERVED_RULES, load_rules

_RULES_DIR = Path(__file__).parent / "rules"
_CONFIG_PREFIX = "# headgate-verify-config:"


def _known_rules() -> set[str]:
    return {rule.id for rule in load_rules()} | {name for name, _ in CHECKS} | set(RESERVED_RULES)


def _cases() -> list[tuple[str, str, Path]]:
    return [
        (rule_dir.name, outcome, entry)
        for rule_dir in sorted(_RULES_DIR.iterdir())
        if rule_dir.is_dir()
        for outcome in ("fail", "pass")
        if (rule_dir / outcome).is_dir()
        for entry in sorted((rule_dir / outcome).iterdir())
        if entry.is_dir() or entry.suffix == ".py"
    ]


def _config(entry: Path) -> Config:
    source = min(entry.rglob("client.py")) if entry.is_dir() else entry
    first = source.read_text(encoding="utf-8").partition("\n")[0]
    if not first.startswith(_CONFIG_PREFIX):
        return Config()
    values = json.loads(first.removeprefix(_CONFIG_PREFIX))
    known = {field.name for field in fields(Config)}
    assert set(values) <= known, f"{entry}: unknown Config fields {sorted(set(values) - known)}"
    return Config(**{name: frozenset(items) for name, items in values.items()})


def _package(entry: Path, tmp_path: Path) -> Path:
    target = tmp_path / "pkg"
    if entry.is_dir():
        shutil.copytree(entry, target)
    else:
        target.mkdir()
        shutil.copyfile(entry, target / "client.py")
    return target


@pytest.mark.parametrize(
    ("rule_id", "outcome", "entry"),
    [pytest.param(*case, id=f"{case[0]}/{case[1]}/{case[2].name}") for case in _cases()],
)
def test_fixture(rule_id: str, outcome: str, entry: Path, tmp_path: Path) -> None:
    """A ``fail`` fixture yields the rule's finding; a ``pass`` fixture yields none of it."""
    findings = verify([_package(entry, tmp_path)], _config(entry))
    own = [finding for finding in findings if finding.rule == rule_id]
    if outcome == "fail":
        assert own, f"expected a {rule_id} finding; got {[finding.render() for finding in findings]}"
    else:
        assert not own, f"expected no {rule_id} finding; got {[finding.render() for finding in own]}"


def test_every_rule_has_fixtures() -> None:
    """Every rule has a ``fail`` and a ``pass`` fixture, and every fixture directory names a rule."""
    known = _known_rules()
    present = {(rule_id, outcome) for rule_id, outcome, _ in _cases()}
    missing = sorted(
        f"{rule_id}/{outcome}" for rule_id in known for outcome in ("fail", "pass") if (rule_id, outcome) not in present
    )
    orphans = sorted(path.name for path in _RULES_DIR.iterdir() if path.is_dir() and path.name not in known)
    assert not missing, f"rules without fixtures: {missing}"
    assert not orphans, f"fixture directories naming no rule: {orphans}"
