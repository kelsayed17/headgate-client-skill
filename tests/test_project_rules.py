# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""Tests for the project's own rules: ``rule-dirs`` in ``[tool.headgate-verify]``, run beside the shipped ones."""

from typing import TYPE_CHECKING

import pytest

from headgate_verify import cli
from headgate_verify.checks import CHECKS
from headgate_verify.config import Config, ConfigError, load_config
from headgate_verify.engine import all_rules, verify
from tests.helpers import write

if TYPE_CHECKING:
    from pathlib import Path

USAGE_ERROR = 2

#: A project rule that reports every call to ``self.forbidden()``.
_RULE = """\
id: {rule_id}
language: python
severity: error
message: a project rule's message
note: the project rule's fix
files:
  - client.py
rule:
  pattern: self.forbidden()
"""

_CLIENT = """\
class C(AsyncBaseClient):
    async def get_x(self) -> None:
        self.forbidden()
"""


def _project(root: Path, rule_id: str = "acme-no-forbidden", client: str = _CLIENT) -> Path:
    """Write a project at ``root``: its pyproject naming ``rules/``, one rule there, and one client package."""
    write(root, "pyproject.toml", '[tool.headgate-verify]\nrule-dirs = ["rules"]\n')
    write(root, f"rules/{rule_id}.yml", _RULE.format(rule_id=rule_id))
    write(root, "clients/acme/client.py", client)
    return root


def test_rule_dirs_resolve_against_the_pyproject(tmp_path: Path) -> None:
    """An entry is relative to the directory holding the pyproject, whatever directory the search starts in."""
    _project(tmp_path)
    nested = tmp_path / "clients" / "acme"
    assert load_config(nested).rule_dirs == frozenset({str((tmp_path / "rules").resolve())})


def test_a_rule_dir_that_is_no_directory_is_config_error(tmp_path: Path) -> None:
    """A missing directory is named in the error, so a typo cannot silently run no project rules."""
    write(tmp_path, "pyproject.toml", '[tool.headgate-verify]\nrule-dirs = ["nope"]\n')
    with pytest.raises(ConfigError, match="'nope'"):
        load_config(tmp_path)


def test_a_project_rule_reports_with_its_message_and_fix(tmp_path: Path) -> None:
    """The project's rule runs over the package beside the shipped ones, carrying its own message and note."""
    config = load_config(_project(tmp_path))
    findings = [finding for finding in verify([tmp_path / "clients"], config) if finding.rule == "acme-no-forbidden"]
    assert [(finding.line, finding.message, finding.fix) for finding in findings] == [
        (3, "a project rule's message", "the project rule's fix"),
    ]


def test_without_the_config_no_project_rule_runs(tmp_path: Path) -> None:
    """The project's rules are the project's: ``verify`` without its config runs only the shipped ones."""
    _project(tmp_path)
    assert not [finding for finding in verify([tmp_path / "clients"]) if finding.rule == "acme-no-forbidden"]


def test_an_allow_comment_names_a_project_rule(tmp_path: Path) -> None:
    """An allow comment may exempt a project rule: its id is a known rule, so the comment is no bad exemption."""
    client = _CLIENT.replace(
        "self.forbidden()", "self.forbidden()  # headgate-verify: allow acme-no-forbidden -- measured safe"
    )
    config = load_config(_project(tmp_path, client=client))
    rules = {finding.rule for finding in verify([tmp_path / "clients"], config)}
    assert not rules & {"acme-no-forbidden", "bad-exemption"}


def test_without_a_config_all_rules_is_the_shipped_set(tmp_path: Path) -> None:
    """``all_rules`` without a config is the shipped set; the project's rules join it only with one."""
    config = load_config(_project(tmp_path))
    assert "acme-no-forbidden" not in {rule.id for rule in all_rules()}
    assert "acme-no-forbidden" in {rule.id for rule in all_rules(config)}


def test_two_project_rules_may_not_share_an_id(tmp_path: Path) -> None:
    """The same id in two rule directories is refused, as a clash with a shipped rule is."""
    _project(tmp_path)
    write(tmp_path, "pyproject.toml", '[tool.headgate-verify]\nrule-dirs = ["rules", "more"]\n')
    write(tmp_path, "more/acme-no-forbidden.yml", _RULE.format(rule_id="acme-no-forbidden"))
    with pytest.raises(ValueError, match="acme-no-forbidden"):
        verify([tmp_path / "clients"], load_config(tmp_path))


def test_a_rule_edited_between_runs_is_read_again(tmp_path: Path) -> None:
    """Rules are read on every run, so one process sees an edit, and a deleted rule stops reporting."""
    config = load_config(_project(tmp_path))
    rule = tmp_path / "rules" / "acme-no-forbidden.yml"
    rule.write_text(_RULE.format(rule_id="acme-no-forbidden").replace("a project rule's message", "edited"))
    assert "edited" in {finding.message for finding in verify([tmp_path / "clients"], config)}
    rule.unlink()
    assert "acme-no-forbidden" not in {finding.rule for finding in verify([tmp_path / "clients"], config)}


@pytest.mark.parametrize(
    ("body", "reason"),
    [
        ("id: acme-bad\nmessage: [unclosed\n", "not valid YAML"),
        (_RULE.format(rule_id="acme-bad").replace("pattern: self.forbidden()", "kind: not_a_real_kind"), "refuses"),
        (_RULE.format(rule_id="acme-bad").replace("pattern: self.forbidden()", "bogus_key: 1"), "refuses"),
    ],
    ids=["malformed-yaml", "unknown-kind", "unknown-key"],
)
def test_a_rule_that_will_not_load_is_a_usage_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], body: str, reason: str
) -> None:
    """A broken rule file is exit 2 naming the file, not a traceback or exit 1, and before any package is read."""
    _project(tmp_path)
    write(tmp_path, "rules/acme-bad.yml", body)
    monkeypatch.chdir(tmp_path)
    assert cli.main(["clients"]) == USAGE_ERROR
    err = capsys.readouterr().err
    assert "acme-bad.yml" in err
    assert reason in err
    assert "checked" not in err


def test_a_yaml_file_is_refused_not_skipped(tmp_path: Path) -> None:
    """A rule saved as ``.yaml`` would silently never run, so it is an error naming the file."""
    _project(tmp_path)
    write(tmp_path, "rules/acme-other.yaml", _RULE.format(rule_id="acme-other"))
    with pytest.raises(ValueError, match=r"acme-other\.yaml"):
        verify([tmp_path / "clients"], load_config(tmp_path))


@pytest.mark.parametrize("taken", ["client-base-url", "bad-exemption", CHECKS[0].rule.id])
def test_a_project_rule_may_not_take_another_rules_id(tmp_path: Path, taken: str) -> None:
    """A shipped rule's, a reserved or a check's id is refused, so an allow comment names exactly one rule."""
    config = load_config(_project(tmp_path, rule_id=taken))
    with pytest.raises(ValueError, match=taken):
        verify([tmp_path / "clients"], config)


def test_a_clash_is_a_usage_error_for_the_command(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The command reports a project rule that takes a shipped id as exit 2 with the reason, not a traceback."""
    _project(tmp_path, rule_id="client-base-url")
    monkeypatch.chdir(tmp_path)
    assert cli.main(["clients"]) == USAGE_ERROR
    assert "client-base-url" in capsys.readouterr().err


def test_the_command_reads_rule_dirs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Run from the project root, the command loads the project's rules and fails on their findings."""
    _project(tmp_path)
    monkeypatch.chdir(tmp_path)
    assert cli.main(["clients"]) == 1
    assert "acme-no-forbidden" in capsys.readouterr().out


def test_the_default_config_has_no_rule_dirs() -> None:
    """With no ``rule-dirs``, only the shipped rules run."""
    assert Config().rule_dirs == frozenset()


def test_a_project_rule_scoped_by_packages_runs_only_there(tmp_path: Path) -> None:
    """``packages:`` in a project rule limits it to the named packages of a project holding several."""
    _project(tmp_path)
    write(tmp_path, "rules/acme-no-forbidden.yml", _RULE.format(rule_id="acme-no-forbidden") + "packages: [acme]\n")
    write(tmp_path, "clients/other/client.py", _CLIENT)
    found = [
        finding
        for finding in verify([tmp_path / "clients"], load_config(tmp_path))
        if finding.rule == "acme-no-forbidden"
    ]
    assert [finding.path.parent.name for finding in found] == ["acme"]
