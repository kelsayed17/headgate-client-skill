# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""Tests for the Python checks: each fail fixture fails for the clause it names, and what fixtures cannot show.

The fixture harness (``test_rule_fixtures.py``) proves a fail fixture yields *a* finding of its rule. Here each fail
fixture of a Python check is pinned to the clause it was written for (a message fragment and a finding count), so a
fixture cannot pass by tripping a different clause. The harness names every package ``pkg``; the cases a fixture
cannot express (another package name, a pyproject above the package, tests under the project root) are built in
``tmp_path``.
"""

import os
import shutil
from pathlib import Path

import pytest
from ast_grep_py import SgRoot

from headgate_verify.checks import CHECKS
from headgate_verify.checks.flavour import detect_flavour
from headgate_verify.checks.models import provider_prefix
from headgate_verify.engine import verify

_RULES_DIR = Path(__file__).parent / "rules"

_CLAUSES: dict[str, tuple[str, int]] = {
    "one-class-per-host/fail/merged_hosts": ("passes an absolute URL on host data.two.example", 2),
    "one-class-per-host/fail/merged_hosts_constant": ("passes an absolute URL on host data.two.example", 1),
    "one-class-per-host/fail/merged_hosts_class_attribute": ("passes an absolute URL on host data.two.example", 1),
    "one-class-per-host/fail/merged_hosts_sibling_constant": ("passes an absolute URL on host b.example", 1),
    "one-class-per-host/fail/shared_base": ("subclasses the client class _Base", 2),
    "one-class-per-host/fail/shared_base_in_another_module": ("subclasses the client class Base", 1),
    "one-class-per-host/fail/shared_mixin": ("has a base besides AsyncBaseClient: _Helpers", 2),
    "one-class-per-host/fail/same_base_url_name": ("shares its base URL name API with class Reads", 1),
    "one-class-per-host/fail/same_host_two_names": ("calls host api.one.example, as class Reads does", 1),
    "one-class-per-host/fail/base_url_literal": ("is not a module-level name", 1),
    "one-class-per-host/fail/base_url_parameter": ("is not a module-level name", 1),
    "one-class-per-host/fail/base_url_attribute": ("is not a module-level name", 1),
    "one-class-per-host/fail/no_base_url": ("passes no base_url= to super().__init__", 1),
    "model-has-no-provider-prefix/fail/prefixed": ("starts with the provider name Pkg", 1),
    "model-has-no-provider-prefix/fail/all_caps_prefix": ("starts with the provider name Pkg", 1),
    "model-has-no-provider-prefix/fail/prefix_alone": ("starts with the provider name Pkg", 1),
    "model-has-no-provider-prefix/fail/nested_class": ("starts with the provider name Pkg", 1),
    "package-layout/fail/no_init": ("has no __init__.py", 1),
    "package-layout/fail/init_reexports": ("__init__.py holds a docstring only", 2),
    "package-layout/fail/init_no_docstring": ("__init__.py holds no docstring", 1),
    "package-layout/fail/no_models": ("has no models.py", 1),
    "package-layout/fail/no_docs_paths": ("has no docs_paths.json", 1),
    "package-layout/fail/no_tests_dir": ("has no tests directory", 1),
    "package-layout/fail/tests_missing_method_names": ("has no test_method_names.py", 1),
    "package-layout/fail/tests_missing_client_tests": ("has no test_client.py", 1),
    "package-layout/fail/paginate_without_pagination": ("calls self.paginate but has no pagination.py", 1),
    "one-flavour/fail/mixed": ("imports both flavours", 1),
    "one-flavour/fail/mixed_headgate_submodule_import": ("imports both flavours", 1),
    "one-flavour/fail/extra_missing": ("does not declare headgate[msgspec]", 1),
    "one-flavour/fail/wrong_extra": ("does not declare headgate[pydantic]", 1),
    "one-flavour/fail/extra_in_a_tool_table": ("does not declare headgate[pydantic]", 1),
    "one-flavour/fail/no_pyproject": ("no pyproject.toml", 1),
    "one-flavour/fail/invalid_toml": ("is not valid TOML", 1),
    "one-flavour/fail/not_utf8": (
        "is not UTF-8 (invalid continuation byte), so it cannot declare headgate[msgspec]",
        1,
    ),
    "one-flavour/fail/project_not_a_table": ("[project] is not a table, so it cannot declare headgate[msgspec]", 1),
    "one-flavour/fail/dependencies_not_a_list": (
        "[project].dependencies is not a list, so it cannot declare headgate[msgspec]",
        1,
    ),
    "one-flavour/fail/optional_dependencies_not_a_table": (
        "[project.optional-dependencies] is not a table, so it cannot declare headgate[msgspec]",
        1,
    ),
    "one-flavour/fail/optional_group_not_a_list": (
        "[project.optional-dependencies].a is not a list, so it cannot declare headgate[msgspec]",
        1,
    ),
    "one-flavour/fail/dependency_groups_not_a_table": (
        "[dependency-groups] is not a table, so it cannot declare headgate[msgspec]",
        1,
    ),
    "one-flavour/fail/dependency_group_not_a_list": (
        "[dependency-groups].dev is not a list, so it cannot declare headgate[msgspec]",
        1,
    ),
    "client-except-needs-review/fail/swallowed": ("must re-raise a headgate.errors type", 1),
    "client-except-needs-review/fail/reraises": ("must re-raise a headgate.errors type", 1),
    "client-except-needs-review/fail/two_handlers": ("must re-raise a headgate.errors type", 2),
    "client-except-needs-review/fail/in_another_module": ("must re-raise a headgate.errors type", 1),
    "client-cache-with-bearer-auth/fail/shared_bearer_auth": (
        "the bearer auth BearerAuth and caches with Partition.SHARED",
        1,
    ),
    "client-cache-with-bearer-auth/fail/shared_cached_token_auth": (
        "the bearer auth _Mint and caches with Partition.SHARED",
        1,
    ),
    "client-cache-with-bearer-auth/fail/shared_subclass_chain": (
        "the bearer auth _Mint and caches with Partition.SHARED",
        1,
    ),
    "client-cache-with-bearer-auth/fail/shared_static_header_bearer": (
        "the bearer auth StaticHeaderAuth and caches with Partition.SHARED",
        1,
    ),
    "client-cache-with-bearer-auth/fail/shared_static_header_keyword": (
        "the bearer auth StaticHeaderAuth and caches with Partition.SHARED",
        1,
    ),
    "client-cache-with-bearer-auth/fail/shared_attribute_spelling": (
        "the bearer auth BearerAuth and caches with Partition.SHARED",
        1,
    ),
    "client-cache-with-bearer-auth/fail/unreadable_partition_constant": (
        "the bearer auth BearerAuth and caches with a partition it cannot read",
        1,
    ),
    "client-cache-with-bearer-auth/fail/unreadable_partition_parameter": (
        "the bearer auth BearerAuth and caches with a partition it cannot read",
        1,
    ),
    "client-cache-with-bearer-auth/fail/unreadable_partition_unpacked": (
        "the bearer auth BearerAuth and caches with a partition it cannot read",
        1,
    ),
    "client-cache-with-bearer-auth/fail/module_cache_passed_as_cache": (
        "the bearer auth BearerAuth and caches with Partition.SHARED",
        1,
    ),
    "client-cache-with-bearer-auth/fail/module_policy_passed_as_policy": (
        "the bearer auth BearerAuth and caches with Partition.SHARED",
        1,
    ),
    "client-cache-with-bearer-auth/fail/module_policy_unreadable_partition": (
        "the bearer auth BearerAuth and caches with a partition it cannot read",
        1,
    ),
}


def _copy(entry: Path, tmp_path: Path) -> Path:
    target = tmp_path / "pkg"
    shutil.copytree(entry, target)
    return target


def _write(root: Path, files: dict[str, str]) -> None:
    for name, text in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def _own(paths: list[Path], rule: str) -> list[str]:
    return [finding.render() for finding in verify(paths) if finding.rule == rule]


def test_every_check_fail_fixture_names_its_clause() -> None:
    """Each fail fixture of a Python check is listed in ``_CLAUSES``, and every listed fixture exists."""
    fixtures = {
        f"{name}/fail/{entry.name}" for name, _ in CHECKS for entry in sorted((_RULES_DIR / name / "fail").iterdir())
    }
    assert fixtures == set(_CLAUSES)


@pytest.mark.parametrize(("fixture", "clause"), list(_CLAUSES.items()), ids=list(_CLAUSES))
def test_fail_fixture_fails_for_its_clause(fixture: str, clause: tuple[str, int], tmp_path: Path) -> None:
    """The fixture's findings of its rule all carry the clause's message, as many as the fixture holds cases."""
    fragment, count = clause
    rule = fixture.split("/", 1)[0]
    own = _own([_copy(_RULES_DIR / fixture, tmp_path)], rule)
    assert len(own) == count, own
    assert all(fragment in finding for finding in own), own


def test_provider_prefix_is_the_package_name_in_pascal_case() -> None:
    """``lda`` gives ``Lda``; ``open_meteo`` gives ``OpenMeteo``."""
    assert provider_prefix("lda") == "Lda"
    assert provider_prefix("open_meteo") == "OpenMeteo"


def test_multi_word_package_prefix(tmp_path: Path) -> None:
    """In package ``open_meteo``, ``OpenMeteoForecast`` is reported and ``Forecast`` is not."""
    package = tmp_path / "open_meteo"
    _write(
        package,
        {
            "client.py": "from headgate import AsyncBaseClient\n",
            "models.py": "class OpenMeteoForecast:\n    pass\n\n\nclass Forecast:\n    pass\n",
        },
    )
    expected = (
        f"{package / 'models.py'}:1 model-has-no-provider-prefix the model class OpenMeteoForecast starts with the "
        "provider name OpenMeteo; the module path already says the provider"
    )
    assert _own([package], "model-has-no-provider-prefix") == [expected]


_COMPLETE_PACKAGE = {
    "__init__.py": '"""The lda client."""\n',
    "client.py": "from headgate import AsyncBaseClient\n",
    "models.py": "",
    "docs_paths.json": "{}\n",
}


def test_tests_under_the_project_root(tmp_path: Path) -> None:
    """A package's tests may live at ``tests/<package name>/`` under the directory of the nearest pyproject."""
    _write(tmp_path, {"pyproject.toml": "[project]\nname = 'x'\n"})
    _write(tmp_path / "src" / "lda", _COMPLETE_PACKAGE)
    _write(tmp_path / "tests" / "lda", {"test_client.py": "", "test_method_names.py": ""})
    assert _own([tmp_path / "src"], "package-layout") == []


def test_tests_under_the_root_need_a_pyproject(tmp_path: Path) -> None:
    """With no pyproject there is no project root: ``tests/lda`` two levels up is neither a root's nor a sibling."""
    _write(tmp_path / "src" / "clients" / "lda", _COMPLETE_PACKAGE)
    _write(tmp_path / "tests" / "lda", {"test_client.py": "", "test_method_names.py": ""})
    (finding,) = _own([tmp_path / "src"], "package-layout")
    assert "has no tests directory" in finding
    assert str(tmp_path / "src" / "clients" / "tests" / "lda") in finding


def test_tests_beside_the_package(tmp_path: Path) -> None:
    """R14: ``<package>/../tests/<package name>/`` holds the tests, as the spec draws it, with no pyproject needed."""
    _write(tmp_path / "clients" / "lda", _COMPLETE_PACKAGE)
    _write(tmp_path / "clients" / "tests" / "lda", {"test_client.py": "", "test_method_names.py": ""})
    assert _own([tmp_path / "clients" / "lda"], "package-layout") == []


def test_tests_beside_the_package_missing_a_file(tmp_path: Path) -> None:
    """A sibling tests directory that exists but lacks a file names the file."""
    _write(tmp_path / "clients" / "lda", _COMPLETE_PACKAGE)
    _write(tmp_path / "clients" / "tests" / "lda", {"test_client.py": ""})
    (finding,) = _own([tmp_path / "clients" / "lda"], "package-layout")
    assert f"the tests directory {tmp_path / 'clients' / 'tests' / 'lda'} has no test_method_names.py" in finding


def test_unreadable_pyproject_is_a_finding(tmp_path: Path) -> None:
    """A pyproject the verifier cannot open is a finding, not a traceback."""
    _write(tmp_path / "lda", {"client.py": "import msgspec\n"})
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[project]\nname = 'x'\ndependencies = ['headgate[msgspec]']\n")
    pyproject.chmod(0)
    try:
        if os.access(pyproject, os.R_OK):
            pytest.skip("this user reads a mode-000 file (root)")
        (finding,) = _own([tmp_path / "lda"], "one-flavour")
    finally:
        pyproject.chmod(0o644)
    assert "cannot be read" in finding
    assert "so it cannot declare headgate[msgspec]" in finding


def test_flavour_extra_declared_in_a_pyproject_above_the_package(tmp_path: Path) -> None:
    """The nearest pyproject at or above the package declares the extra."""
    _write(tmp_path, {"pyproject.toml": "[project]\nname = 'x'\ndependencies = ['headgate[msgspec]>=0.7.0']\n"})
    _write(tmp_path / "src" / "lda", {"client.py": "import msgspec\n"})
    assert _own([tmp_path / "src"], "one-flavour") == []


def _modules(sources: dict[str, str]) -> dict[Path, SgRoot]:
    return {Path(name): SgRoot(text, "python") for name, text in sources.items()}


@pytest.mark.parametrize(
    ("sources", "expected"),
    [
        ({"client.py": "import msgspec.json as mj\n"}, "msgspec"),
        ({"client.py": "from headgate.msgspec import decoder\n"}, "msgspec"),
        ({"client.py": "from headgate import AsyncBaseClient, msgspec\n"}, "msgspec"),
        ({"models.py": "import pydantic\n"}, "pydantic"),
        ({"models.py": "from pydantic import BaseModel\n"}, "pydantic"),
        ({"client.py": "from headgate import pydantic as hp\n"}, "pydantic"),
        ({"client.py": "import headgate.pydantic\n"}, "pydantic"),
        ({"client.py": "import msgspecx\nfrom pydantic_settings import X\nfrom headgate import as_bytes\n"}, None),
        ({"client.py": "import msgspec\n", "models.py": "import pydantic\n"}, None),
    ],
)
def test_detect_flavour(sources: dict[str, str], expected: str | None) -> None:
    """A flavour is detected from its imports; neither, or both, is ``None``."""
    assert detect_flavour(_modules(sources)) == expected


def test_check_findings_honour_allow_comments(tmp_path: Path) -> None:
    """An allow comment drops a check's finding as it does a YAML rule's: on its line, or above the first statement."""
    _write(
        tmp_path / "lda",
        {
            "client.py": "# headgate-verify: allow package-layout -- layout checked elsewhere\n"
            "from headgate import AsyncBaseClient\n",
            "models.py": "class LdaFiling:  # headgate-verify: allow model-has-no-provider-prefix -- the API's name\n"
            "    pass\n",
        },
    )
    rules = {finding.rule for finding in verify([tmp_path / "lda"])}
    assert not rules & {"model-has-no-provider-prefix", "package-layout", "bad-exemption"}, rules
