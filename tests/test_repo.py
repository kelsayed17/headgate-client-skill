# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""Repository gates: the skill's links resolve, its generated rule list is current, and the plugin names the skill."""

import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from headgate_verify.checks import CHECKS
from headgate_verify.engine import verify

if TYPE_CHECKING:
    from types import ModuleType

ROOT = Path(__file__).parent.parent
SKILL = ROOT / "skills" / "building-headgate-clients"
GENERATOR = ROOT / "scripts" / "gen_rule_docs.py"
FORBIDDEN = b"pri" + b"sm"
"""Built from two halves, so this file never spells the word it forbids."""
EXEMPT = frozenset({"CHANGELOG.md"})
"""The one file allowed the word: the changelog's credits."""
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
FRONTMATTER = re.compile(r"\A---\n(?P<body>.*?)\n---\n", re.DOTALL)
DESCRIPTION_START = "Use when building, extending or reviewing an HTTP API client on headgate"


def _repo_files() -> list[Path]:
    """Return every file git tracks or would track: tracked, plus untracked files no ignore rule hides."""
    git = shutil.which("git")
    assert git is not None, "git is needed to list the repository's files"
    listed = subprocess.run(  # noqa: S603 -- a fixed git command over this repository
        [git, "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout
    return [ROOT / name for name in listed.decode().split("\0") if name and (ROOT / name).is_file()]


def _generator() -> ModuleType:
    spec = importlib.util.spec_from_file_location("gen_rule_docs", GENERATOR)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _frontmatter(path: Path) -> dict[str, str]:
    match = FRONTMATTER.match(path.read_text(encoding="utf-8"))
    assert match is not None, f"{path} has no YAML frontmatter"
    pairs = (line.partition(":") for line in match["body"].splitlines() if line.strip())
    return {key.strip(): value.strip() for key, _, value in pairs}


def test_no_forbidden_strings() -> None:
    """No file of the repository outside ``EXEMPT`` names the project the conventions came from."""
    offenders = [
        str(path.relative_to(ROOT))
        for path in _repo_files()
        if path.relative_to(ROOT).as_posix() not in EXEMPT and FORBIDDEN in path.read_bytes().lower()
    ]
    assert not offenders, f"files naming it: {offenders}"


def test_skill_links_resolve() -> None:
    """Every relative link in ``SKILL.md`` and the references names a file or directory that exists."""
    documents = [SKILL / "SKILL.md", *sorted((SKILL / "references").glob("*.md"))]
    broken: list[str] = []
    checked = 0
    for document in documents:
        for target in LINK.findall(document.read_text(encoding="utf-8")):
            if re.match(r"^[a-z][a-z0-9+.-]*:", target) or target.startswith("#"):
                continue
            checked += 1
            if not (document.parent / target.partition("#")[0]).exists():
                broken.append(f"{document.relative_to(ROOT)} -> {target}")
    assert checked, "the skill links to nothing"
    assert not broken, f"broken links: {broken}"


def test_skill_links_every_reference() -> None:
    """``SKILL.md`` links each of its references, so none is unreachable from the skill."""
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    unlinked = [
        path.name for path in sorted((SKILL / "references").glob("*.md")) if f"(references/{path.name})" not in text
    ]
    assert not unlinked, f"references SKILL.md never links: {unlinked}"


def test_skill_frontmatter() -> None:
    """The skill is named ``building-headgate-clients`` and says when to use it."""
    frontmatter = _frontmatter(SKILL / "SKILL.md")
    assert frontmatter["name"] == "building-headgate-clients"
    assert frontmatter["description"].startswith(DESCRIPTION_START)


def test_rule_docs_current() -> None:
    """``references/verifier.md`` is what ``scripts/gen_rule_docs.py`` writes today."""
    result = subprocess.run(  # noqa: S603 -- this interpreter running the repository's own script
        [sys.executable, str(GENERATOR), "--check"], cwd=ROOT, check=False, capture_output=True, text=True
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_rule_docs_check_fails_when_stale(tmp_path: Path) -> None:
    """``--check`` exits non-zero on a stale file and leaves it as it was; a plain run rewrites it."""
    generator = _generator()
    stale = tmp_path / "verifier.md"
    stale.write_text("stale\n", encoding="utf-8")

    assert generator.main(["--check", "--output", str(stale)]) == 1
    assert stale.read_text(encoding="utf-8") == "stale\n"
    assert generator.main(["--output", str(stale)]) == 0
    assert generator.main(["--check", "--output", str(stale)]) == 0


def test_rule_docs_list_every_rule() -> None:
    """The generated list names every YAML rule and every check, with its severity and its fix."""
    generator = _generator()
    text = generator.render()
    for row in generator.rows():
        assert f"| `{row.id}` | {row.severity} |" in text
        assert row.fix
        assert f"| `{row.id}` | {row.fix.replace('|', chr(92) + '|')} |" in text


@pytest.mark.parametrize(("rule_id", "expected"), [(check.rule.id, check.rule.severity) for check in CHECKS])
def test_check_severity_is_documented(rule_id: str, expected: str, tmp_path: Path) -> None:
    """A check's documented severity is the one its findings carry on its ``fail`` fixtures."""
    severities: set[str] = set()
    for entry in sorted((ROOT / "tests" / "rules" / rule_id / "fail").iterdir()):
        target = tmp_path / entry.stem / "pkg"  # the name the fixture harness gives a package
        if entry.is_dir():
            shutil.copytree(entry, target)
        elif entry.suffix == ".py":
            target.mkdir(parents=True)
            shutil.copyfile(entry, target / "client.py")
        else:
            continue
        severities |= {finding.severity for finding in verify([target]) if finding.rule == rule_id}
    assert severities == {expected}


def test_plugin_manifest_names_the_skill() -> None:
    """The plugin manifest is complete, versioned with the package, and its default ``skills/`` holds the skill."""
    manifest = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]

    assert manifest["name"] == "headgate-client-skill"
    assert manifest["version"] == project["version"]
    assert manifest["author"] == {"name": "Khaled Elsayed"}
    assert manifest["license"] == project["license"]
    assert manifest["description"]
    assert manifest["homepage"] == manifest["repository"] == "https://github.com/kelsayed17/headgate-client-skill"
    skills = sorted(path.parent.name for path in (ROOT / "skills").glob("*/SKILL.md"))
    assert skills == ["building-headgate-clients"]


def test_ruff_setting_the_examples_need_is_taught() -> None:
    """The conventions quote the ruff setting the examples' models rely on, with this repository's values."""
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    bases = pyproject["tool"]["ruff"]["lint"]["flake8-type-checking"]["runtime-evaluated-base-classes"]
    conventions = (SKILL / "references" / "conventions.md").read_text(encoding="utf-8")
    assert f"runtime-evaluated-base-classes = {json.dumps(bases)}" in conventions
