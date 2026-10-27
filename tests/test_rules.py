# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""Tests for the YAML rule engine, parse errors and allow comments."""

from importlib.resources import files
from pathlib import Path

import pytest
from ast_grep_py import SgRoot

from headgate_verify.config import Config
from headgate_verify.engine import verify
from headgate_verify.exemptions import apply_exemptions
from headgate_verify.package import find_packages
from headgate_verify.rules import load_rules, parse, rule_from_yaml, run_rules

_FIXTURES = Path(__file__).parent / "rules"

_FILLER_RULE = """\
id: filler-name
message: a name is a filler word
severity: warning
rule:
  kind: identifier
  regex: '^({{config.filler_words}})$'
"""


def _write(root: Path, name: str, text: str) -> Path:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_shipped_rules_load_and_compile() -> None:
    """Every shipped YAML rule loads, its id is its file stem, and ast-grep accepts its config."""
    rules = load_rules()
    stems = sorted(path.name.removesuffix(".yml") for path in files("headgate_verify").joinpath("rules").iterdir())
    assert sorted(rule.id for rule in rules) == stems
    assert "client-module-has-a-client" in stems
    for rule in rules:
        SgRoot("", "python").root().find_all(rule.config)


def test_client_module_rule_shape() -> None:
    """The ported rule is an error scoped to client.py."""
    (rule,) = [rule for rule in load_rules() if rule.id == "client-module-has-a-client"]
    assert rule.severity == "error"
    assert rule.files == ("client.py",)


def test_id_must_match_the_stem() -> None:
    """A rule whose ``id:`` differs from its file name is refused."""
    with pytest.raises(ValueError, match="other"):
        rule_from_yaml(_FILLER_RULE, "other")


def test_files_default_and_severity_mapping() -> None:
    """``files`` defaults to every module; ast-grep's ``warning`` maps onto the warning severity."""
    rule = rule_from_yaml(_FILLER_RULE, "filler-name")
    assert rule.files == ("**/*.py",)
    assert rule.severity == "warning"
    with pytest.raises(ValueError, match="severity"):
        rule_from_yaml(_FILLER_RULE.replace("warning", "hint"), "filler-name")


def test_unknown_placeholder_is_refused() -> None:
    """A placeholder naming no Config field is refused at load time."""
    with pytest.raises(ValueError, match="no_such_field"):
        rule_from_yaml(_FILLER_RULE.replace("filler_words", "no_such_field"), "filler-name")


def test_config_placeholder_writes_an_alternation(tmp_path: Path) -> None:
    """``{{config.<field>}}`` becomes an escaped alternation of the field's values; an empty field matches nothing."""
    _write(tmp_path, "client.py", "api = 1\nv2 = 2\nkeep = 3\na_b = 4\n")
    (pkg,) = find_packages([tmp_path])
    rule = rule_from_yaml(_FILLER_RULE, "filler-name")
    found = run_rules(pkg, [rule], Config(filler_words=frozenset({"api", "v2"})))
    assert [(finding.line, finding.severity) for finding in found] == [(1, "warning"), (2, "warning")]
    assert run_rules(pkg, [rule], Config(filler_words=frozenset())) == []


def test_files_globs_scope_a_rule(tmp_path: Path) -> None:
    """A rule reads only the modules its ``files`` globs name, relative to the package root."""
    _write(tmp_path, "client.py", "api = 1\n")
    _write(tmp_path, "models.py", "api = 1\n")
    (pkg,) = find_packages([tmp_path])
    rule = rule_from_yaml(_FILLER_RULE.replace("rule:", "files: [models.py]\nrule:"), "filler-name")
    found = run_rules(pkg, [rule], Config())
    assert [finding.path.name for finding in found] == ["models.py"]


def test_unparseable_file_is_a_finding(tmp_path: Path) -> None:
    """An unparseable module is one parse-error finding and nothing else; the modules beside it are still checked."""
    client = _write(tmp_path, "client.py", "def (:\n")
    _write(tmp_path, "models.py", "x = 1\n")
    (pkg,) = find_packages([tmp_path])
    assert list(parse(pkg)) == [tmp_path / "models.py"]
    findings = verify([tmp_path])
    assert [(finding.rule, finding.path, finding.line, finding.severity) for finding in findings] == [
        ("parse-error", client, 1, "error"),
    ]


def test_reasoned_allow_silences_the_finding(tmp_path: Path) -> None:
    """A reasoned allow comment drops the finding it covers and reports nothing in its place."""
    package = tmp_path / "pkg"
    package.mkdir()
    (package / "client.py").write_text((_FIXTURES / "bad-exemption/pass/reasoned_allow.py").read_text())
    assert verify([package]) == []
    (package / "client.py").write_text('"""No allow comment."""\n')
    assert [finding.rule for finding in verify([package])] == ["client-module-has-a-client"]


def test_allow_on_the_enclosing_def_line(tmp_path: Path) -> None:
    """An allow comment on the ``def`` line covers a finding inside the function body."""
    _write(
        tmp_path,
        "client.py",
        "from headgate import AsyncBaseClient\n\n\nclass C(AsyncBaseClient):\n    pass\n\n\n"
        "def f():  # headgate-verify: allow filler-name -- a reason\n    api = 1\n",
    )
    (pkg,) = find_packages([tmp_path])
    rule = rule_from_yaml(_FILLER_RULE, "filler-name")
    raw = run_rules(pkg, [rule], Config(filler_words=frozenset({"api"})))
    assert [finding.line for finding in raw] == [9]
    assert apply_exemptions(raw, parse(pkg), frozenset({"filler-name"})) == []
    unknown = apply_exemptions(raw, parse(pkg), frozenset())
    assert [(finding.rule, finding.line) for finding in unknown] == [("bad-exemption", 8), ("filler-name", 9)]
