# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""The recording fixtures in a real suite: a replay answers with placeholders; a recording keeps the operator's.

pytest-recording's ``record_mode`` is ``none`` here (nothing passed ``--record-mode``), so the module's tests replay;
the class below overrides it to record.
"""

from typing import TYPE_CHECKING

import pytest

from headgate_verify.testing import creds, plugin
from headgate_verify.testing.recording import (  # a fixture imported into a module is registered
    Recording,
    no_retry_backoff,  # noqa: F401 -- a fixture imported into a module is registered there
    replay_credentials,  # noqa: F401 -- as above
)

if TYPE_CHECKING:
    from collections.abc import Iterator

RECORDING = Recording(placeholders={("demo", "key"): "replay-demo-key"})


@pytest.fixture
def recording() -> Recording:
    """Return the module's recording settings."""
    return RECORDING


@pytest.fixture(autouse=True)
def operator() -> Iterator[None]:
    """Install the operator's provider before the recording fixtures run."""
    previous = creds.use(lambda _provider, _name: "operator-value")
    yield
    creds.use(previous)


def test_a_replay_answers_each_credential_with_its_placeholder() -> None:
    """A replay answers each credential with its placeholder."""
    assert creds.require("demo", "key") == {"key": "replay-demo-key"}
    assert creds.lookup("demo", "other") is None


class TestRecording:
    """The same fixtures with pytest-recording's ``record_mode`` set to record."""

    @pytest.fixture
    def record_mode(self) -> str:
        """Record rather than replay."""
        return "once"

    def test_a_recording_keeps_the_operator_s_provider(self) -> None:
        """A recording keeps the operator's provider."""
        assert creds.lookup("demo", "key") == "operator-value"


def test_the_plugin_adds_the_option_and_installs_the_provider() -> None:
    """The plugin adds the option and installs the provider."""
    added: list[str] = []

    class Parser:
        def addoption(self, name: str, **_: object) -> None:
            added.append(name)

        def addini(self, name: str, *_: object, **__: object) -> None:
            added.append(name)

    class Config:
        def __init__(self, option: str | None, ini: str) -> None:
            self.option, self.ini = option, ini

        def getoption(self, _name: str) -> str | None:
            return self.option

        def getini(self, _name: str) -> str:
            return self.ini

    plugin.pytest_addoption(Parser())  # ty: ignore[invalid-argument-type]  # a duck parser
    assert added == ["--credentials-provider", "credentials_provider"]
    previous = creds.use(None)
    try:
        plugin.pytest_configure(Config(None, "os.path:join"))  # ty: ignore[invalid-argument-type]  # a duck config
        assert creds.lookup("a", "b") == "a/b"
        plugin.pytest_configure(Config(None, ""))  # ty: ignore[invalid-argument-type]  # a duck config
        assert creds.lookup("a", "b") is None
    finally:
        creds.use(previous)
