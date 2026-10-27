# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""Tests for the YAML rule engine, parse errors and allow comments."""

from importlib.resources import files
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from ast_grep_py import SgRoot

from headgate_verify import parsing
from headgate_verify.checks import CHECKS
from headgate_verify.config import Config
from headgate_verify.engine import verify
from headgate_verify.exemptions import apply_exemptions
from headgate_verify.package import find_packages
from headgate_verify.parsing import parse_package
from headgate_verify.rules import load_rules, rule_from_yaml, run_rules

if TYPE_CHECKING:
    from headgate_verify.finding import Finding
    from headgate_verify.package import Package
    from headgate_verify.rules import YamlRule

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


def _run(pkg: Package, rule: YamlRule, config: Config) -> list[Finding]:
    """Return ``rule``'s findings over the modules of ``pkg`` that parse."""
    return run_rules(pkg, parse_package(pkg).modules, [rule], config)


def _verify(paths: list[Path]) -> list[Finding]:
    """Return ``verify(paths)`` without ``package-layout``: these tests' packages are single modules on purpose."""
    return [finding for finding in verify(paths) if finding.rule != "package-layout"]


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
    found = _run(pkg, rule, Config(filler_words=frozenset({"api", "v2"})))
    assert [(finding.line, finding.severity) for finding in found] == [(1, "warning"), (2, "warning")]
    assert _run(pkg, rule, Config(filler_words=frozenset())) == []


def test_files_globs_scope_a_rule(tmp_path: Path) -> None:
    """A rule reads only the modules its ``files`` globs name, relative to the package root."""
    _write(tmp_path, "client.py", "api = 1\n")
    _write(tmp_path, "models.py", "api = 1\n")
    (pkg,) = find_packages([tmp_path])
    rule = rule_from_yaml(_FILLER_RULE.replace("rule:", "files: [models.py]\nrule:"), "filler-name")
    found = _run(pkg, rule, Config())
    assert [finding.path.name for finding in found] == ["models.py"]


def test_skip_packages_in_exempts_a_package_by_name(tmp_path: Path) -> None:
    """A rule with ``skip-packages-in: <field>`` does not run in a package whose directory is named in that field."""
    _write(tmp_path / "cboe", "client.py", "api = 1\n")
    _write(tmp_path / "fred", "client.py", "api = 1\n")
    pkgs = find_packages([tmp_path])
    rule = rule_from_yaml(
        _FILLER_RULE.replace("rule:", "skip-packages-in: browser_user_agent_packages\nrule:"), "filler-name"
    )
    config = Config(browser_user_agent_packages=frozenset({"cboe"}))
    found = [finding for pkg in pkgs for finding in _run(pkg, rule, config)]
    assert [finding.path.parent.name for finding in found] == ["fred"]
    with pytest.raises(ValueError, match="no_such_field"):
        rule_from_yaml(_FILLER_RULE.replace("rule:", "skip-packages-in: no_such_field\nrule:"), "filler-name")


def test_unparseable_file_is_a_finding(tmp_path: Path) -> None:
    """An unparseable module is one parse-error finding and nothing else; the modules beside it are still checked."""
    client = _write(tmp_path, "client.py", "def (:\n")
    _write(tmp_path, "models.py", "x = 1\n")
    (pkg,) = find_packages([tmp_path])
    assert list(parse_package(pkg).modules) == [tmp_path / "models.py"]
    findings = _verify([tmp_path])
    assert [(finding.rule, finding.path, finding.line, finding.severity) for finding in findings] == [
        ("parse-error", client, 1, "error"),
    ]


def test_reasoned_allow_silences_the_finding(tmp_path: Path) -> None:
    """A reasoned allow comment drops the finding it covers and reports nothing in its place."""
    package = tmp_path / "pkg"
    package.mkdir()
    (package / "client.py").write_text((_FIXTURES / "bad-exemption/pass/reasoned_allow.py").read_text())
    assert _verify([package]) == []
    (package / "client.py").write_text('"""No allow comment."""\n')
    assert [finding.rule for finding in _verify([package])] == ["client-module-has-a-client"]


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
    raw = _run(pkg, rule, Config(filler_words=frozenset({"api"})))
    assert [finding.line for finding in raw] == [9]
    assert apply_exemptions(raw, parse_package(pkg).modules, frozenset({"filler-name"})) == []
    unknown = apply_exemptions(raw, parse_package(pkg).modules, frozenset())
    assert [(finding.rule, finding.line) for finding in unknown] == [("bad-exemption", 8), ("filler-name", 9)]


def test_missing_node_is_a_parse_error(tmp_path: Path) -> None:
    """Code tree-sitter repairs with a MISSING node, but Python refuses, is a parse-error at Python's line."""
    client = _write(tmp_path, "client.py", '"""Doc."""\n\n\ndef f(:\n    pass\n')
    findings = _verify([tmp_path])
    assert [(finding.rule, finding.path, finding.line) for finding in findings] == [("parse-error", client, 4)]


def test_module_finding_is_covered_from_the_leading_block(tmp_path: Path) -> None:
    """A finding against the module is covered by an allow comment anywhere before the first statement."""
    header = "# Copyright (c) 2026 Example Author\n# SPDX-License-Identifier: MIT\n"
    allow = "# headgate-verify: allow client-module-has-a-client -- generated\n"
    _write(tmp_path, "client.py", f'{header}\n{allow}"""Doc."""\n')
    assert _verify([tmp_path]) == []
    _write(tmp_path, "client.py", f'{header}"""Doc."""\n{allow}')
    assert [(finding.rule, finding.line) for finding in _verify([tmp_path])] == [
        ("client-module-has-a-client", 1),
        ("bad-exemption", 4),
    ]


def test_unreadable_module_is_a_parse_error(tmp_path: Path) -> None:
    """A module that cannot be read (here a dangling symlink) is a parse-error finding, not a traceback."""
    client = _write(tmp_path, "client.py", '"""Doc."""\n')
    dangling = tmp_path / "models.py"
    dangling.symlink_to(tmp_path / "gone.py")
    findings = _verify([tmp_path])
    assert [(finding.rule, finding.path, finding.line) for finding in findings] == [
        ("client-module-has-a-client", client, 1),
        ("parse-error", dangling, 1),
    ]
    assert "cannot be read" in findings[1].message


@pytest.mark.parametrize("error", [RecursionError, MemoryError])
def test_parser_exhaustion_is_a_parse_error(
    error: type[Exception], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A module too deep or too large for Python's parser is a parse-error finding, not a traceback."""
    client = _write(tmp_path, "client.py", '"""Doc."""\n')

    def refuse(*_args: object, **_kwargs: object) -> None:
        raise error

    monkeypatch.setattr(parsing.ast, "parse", refuse)
    findings = _verify([tmp_path])
    assert [(finding.rule, finding.path) for finding in findings] == [("parse-error", client)]
    assert error.__name__ in findings[0].message


def test_yaml_finding_carries_the_rule_note_as_its_fix(tmp_path: Path) -> None:
    """A YAML rule's ``note`` reaches its findings as ``fix``."""
    _write(tmp_path, "client.py", '"""No client class."""\n')
    (finding,) = _verify([tmp_path])
    note = {rule.id: rule.fix for rule in load_rules()}["client-module-has-a-client"]
    assert finding.rule == "client-module-has-a-client"
    assert note
    assert finding.fix == note


def test_note_is_loaded_and_optional() -> None:
    """``note`` is read onto the rule as its fix, folded to one line; a rule without one has an empty fix."""
    assert rule_from_yaml(_FILLER_RULE, "filler-name").fix == ""
    noted = rule_from_yaml(_FILLER_RULE + "note: >-\n  Rename it\n  to a word.\n", "filler-name")
    assert noted.fix == "Rename it to a word."


def test_every_shipped_rule_and_check_has_a_fix() -> None:
    """Every YAML rule has a note and every Python check a fix sentence."""
    assert [rule.id for rule in load_rules() if not rule.fix.strip()] == []
    assert [check.rule.id for check in CHECKS if not check.rule.fix.strip()] == []
