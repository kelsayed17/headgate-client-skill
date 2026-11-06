# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""Tests for the credentials provider: what is handed out, what skips, and the pytest option that names it."""

import subprocess
import sys
from typing import TYPE_CHECKING

import pytest

from headgate_verify.testing import creds

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path


@pytest.fixture(autouse=True)
def no_provider() -> Iterator[None]:
    """Each test starts with no provider and restores whatever was installed."""
    previous = creds.use(None)
    try:
        yield
    finally:
        creds.use(previous)


def _answers(table: dict[tuple[str, str], str]) -> creds.CredentialsProvider:
    return lambda provider, name: table.get((provider, name))


def test_require_returns_each_value_and_remembers_it() -> None:
    """Require returns each value and remembers it."""
    creds.use(_answers({("demo", "key"): "k-123456", ("demo", "secret"): "s-654321"}))
    assert creds.require("demo", "key", "secret") == {"key": "k-123456", "secret": "s-654321"}
    assert {"k-123456", "s-654321"} <= creds.handed_out()


def test_a_missing_credential_skips_inside_a_test_naming_each_one() -> None:
    """A missing credential skips inside a test naming each one."""
    creds.use(_answers({("demo", "key"): ""}))
    with pytest.raises(pytest.skip.Exception, match=r"demo\.key and demo\.secret"):
        creds.require("demo", "key", "secret")


def test_a_missing_credential_raises_outside_a_test(monkeypatch: pytest.MonkeyPatch) -> None:
    """A missing credential raises outside a test."""
    monkeypatch.delenv("PYTEST_CURRENT_TEST")
    with pytest.raises(creds.MissingCredentialError, match=r"demo\.key"):
        creds.require("demo", "key")


def test_lookup_answers_none_rather_than_skipping() -> None:
    """Lookup answers none rather than skipping."""
    assert creds.lookup("demo", "key") is None
    creds.use(_answers({("demo", "key"): "looked-up"}))
    assert creds.lookup("demo", "key") == "looked-up"


def test_use_returns_the_provider_it_replaces() -> None:
    """Use returns the provider it replaces."""
    first = _answers({})
    assert creds.use(first) is None
    assert creds.use(None) is first


@pytest.mark.parametrize(
    ("raw", "expected"), [("TRUE", True), (" 1 ", True), ("yes", True), ("false", False), ("0", False), ("No", False)]
)
def test_as_flag_reads_the_usual_spellings(raw: str, expected: bool) -> None:  # noqa: FBT001 -- a parametrized expectation
    """As flag reads the usual spellings."""
    assert creds.as_flag("demo", "live", raw) is expected


def test_as_flag_rejects_anything_else() -> None:
    """As flag rejects anything else."""
    with pytest.raises(ValueError, match=r"demo\.live is 'maybe'"):
        creds.as_flag("demo", "live", "maybe")


def test_a_secret_never_shows_its_value() -> None:
    """A secret never shows its value."""
    secret = creds.Secret("hunter2-hunter2")
    assert "hunter2" not in repr(secret)
    assert secret.get_secret_value() == "hunter2-hunter2"


def test_load_provider_imports_module_function() -> None:
    """Load provider imports module function."""
    assert creds.load_provider("os.path:join") is __import__("os").path.join


@pytest.mark.parametrize("spec", ["os.path", ":join", "os.path:"])
def test_load_provider_refuses_a_spec_without_module_and_function(spec: str) -> None:
    """Load provider refuses a spec without module and function."""
    with pytest.raises(ValueError, match="module:function"):
        creds.load_provider(spec)


def test_load_provider_refuses_a_non_callable() -> None:
    """Load provider refuses a non callable."""
    with pytest.raises(TypeError, match="os:sep is not callable"):
        creds.load_provider("os:sep")


def test_the_user_agent_defaults_its_product_and_scrubs_only_its_contact() -> None:
    """The user agent defaults its product and scrubs only its contact."""
    assert creds.user_agent("demo-tests/1.0").header() == "demo-tests/1.0"
    creds.use(_answers({("user_agent", "product"): "ops/2.0", ("user_agent", "contact"): "ops@example.test"}))
    agent = creds.user_agent("demo-tests/1.0")
    assert agent.header() == "ops/2.0 (+mailto:ops@example.test)"
    assert "ops@example.test" in creds.handed_out()
    assert "ops/2.0" not in creds.handed_out()


@pytest.mark.parametrize(
    ("contact", "expected"),
    [
        ("", ""),
        ("  ", ""),
        ("https://example.test/about", "https://example.test/about"),
        ("mailto:a@b.test", "mailto:a@b.test"),
    ],
)
def test_a_contact_that_is_already_a_uri_is_kept(contact: str, expected: str) -> None:
    """A contact that is already a uri is kept."""
    assert creds.UserAgent("p/1", contact).normalized_contact() == expected


def test_the_plugin_installs_the_named_provider(tmp_path: Path) -> None:
    """``--credentials-provider`` and the ini option, in a pytest run of their own (the option is read at startup)."""
    (tmp_path / "ops_secrets.py").write_text(
        "def lookup(provider, name):\n    return 'from-' + provider + '-' + name\n", encoding="utf-8"
    )
    (tmp_path / "conftest.py").write_text('pytest_plugins = ["headgate_verify.testing.plugin"]\n', encoding="utf-8")
    (tmp_path / "test_live.py").write_text(
        "from headgate_verify.testing import creds\n\n"
        "def test_live():\n    assert creds.require('demo', 'key') == {'key': 'from-demo-key'}\n",
        encoding="utf-8",
    )

    def run(*args: str) -> subprocess.CompletedProcess[str]:
        command = [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "-q", "-rs", *args]
        return subprocess.run(command, cwd=tmp_path, capture_output=True, text=True, check=False)  # noqa: S603 -- this interpreter, over files the test wrote

    assert "1 passed" in run("--credentials-provider", "ops_secrets:lookup").stdout
    (tmp_path / "pytest.ini").write_text("[pytest]\ncredentials_provider = ops_secrets:lookup\n", encoding="utf-8")
    assert "1 passed" in run().stdout
    (tmp_path / "pytest.ini").unlink()
    assert "no credential for demo.key" in run().stdout
