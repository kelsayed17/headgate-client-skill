# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""A live test's credentials and User-Agent contact, from wherever the operator keeps them.

A client's tests name no environment variable, file or vault. A live test or a recording asks for a credential by
provider and field (``lda.api_key``), and a *credentials provider* answers: any callable
``(provider, field) -> str | None``, named as ``module:function`` with ``pytest --credentials-provider`` (or the
``credentials_provider`` ini option, both from :mod:`headgate_verify.testing.plugin`). Where that function reads from
(the environment, a file, a password manager) is the operator's code, outside the repository.

**A missing credential skips, naming it.** No provider configured, or one that answers ``None`` or ``""``, is
``pytest.skip("no credential for lda.api_key ...")`` inside a test (:func:`require`). Outside one
(``PYTEST_CURRENT_TEST`` unset) it is a :class:`MissingCredentialError` with the same names.

**Every value handed out is remembered** (:func:`handed_out`), so a recording scrubs its cassettes of exactly the
secrets and the contact the clients were given (:mod:`headgate_verify.testing.recording`). Nothing here runs at
import, and no offline test needs a key.

A package wraps what it asks for in its own typed credentials, one small function per provider::

    @dataclass(frozen=True, slots=True)
    class LdaCredentials:
        api_key: Secret

    def lda_creds() -> LdaCredentials:
        return LdaCredentials(api_key=Secret(require("lda", "api_key")["api_key"]))
"""

import importlib
import os
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import cast

import pytest

__all__ = [
    "CredentialsProvider",
    "MissingCredentialError",
    "Secret",
    "UserAgent",
    "as_flag",
    "handed_out",
    "load_provider",
    "lookup",
    "require",
    "use",
    "user_agent",
]

#: Answers ``(provider, field)`` with the credential's value, or ``None`` when it has none.
type CredentialsProvider = Callable[[str, str], str | None]

_provider: CredentialsProvider | None = None
_handed_out: set[str] = set()


class MissingCredentialError(RuntimeError):
    """A credential a live client needs has no value, raised outside a test; the message names each one."""


@dataclass(frozen=True, slots=True)
class Secret:
    """A credential value that never shows in a ``repr`` or a traceback (it reads ``Secret()``)."""

    _value: str = field(repr=False)

    def get_secret_value(self) -> str:
        """Return the value itself."""
        return self._value


def use(provider: CredentialsProvider | None) -> CredentialsProvider | None:
    """Make *provider* the one every credential is read from, returning the one it replaces.

    ``None`` leaves every credential missing. A test that swaps the provider restores the returned one.
    """
    global _provider  # one provider per process, set at startup or swapped by a test
    previous, _provider = _provider, provider
    return previous


def load_provider(spec: str) -> CredentialsProvider:
    """Import ``module:function`` and return the function, refusing a spec that names no callable."""
    module_name, sep, attribute = spec.partition(":")
    if not sep or not module_name or not attribute:
        msg = f"a credentials provider is named module:function, not {spec!r}"
        raise ValueError(msg)
    provider: object = getattr(importlib.import_module(module_name), attribute)
    if not callable(provider):
        msg = f"{spec} is not callable"
        raise TypeError(msg)
    return cast("CredentialsProvider", provider)


def handed_out() -> frozenset[str]:
    """Every secret value this module has returned so far, for a recording's scrub."""
    return frozenset(_handed_out)


def _value(provider: str, name: str, *, secret: bool = True) -> str | None:
    value = _provider(provider, name) if _provider is not None else None
    if value is None or value == "":
        return None
    if secret:
        _handed_out.add(value)
    return value


def lookup(provider: str, name: str) -> str | None:
    """Return one credential, or ``None`` when it has none: for a caller that has a placeholder and must not skip."""
    return _value(provider, name)


def require(provider: str, *names: str) -> dict[str, str]:
    """Return ``{name: value}`` for each of *provider*'s *names*, skipping the test (or raising) naming any missing."""
    values = {name: _value(provider, name) for name in names}
    missing = [f"{provider}.{name}" for name, value in values.items() if value is None]
    if missing:
        names_text = " and ".join(missing)
        if "PYTEST_CURRENT_TEST" in os.environ:
            pytest.skip(f"no credential for {names_text}: run with --credentials-provider module:function")
        msg = f"no credential for {names_text} to reach the live {provider} API (--credentials-provider)"
        raise MissingCredentialError(msg)
    return {name: value for name, value in values.items() if value is not None}


def as_flag(provider: str, name: str, raw: str) -> bool:
    """Read the credential *raw* (``provider.name``) as a boolean: ``true``/``1``/``yes`` or ``false``/``0``/``no``.

    A malformed value is a mistake to fix, not a reason to skip, so it raises :class:`ValueError`.
    """
    match raw.strip().lower():
        case "true" | "1" | "yes":
            return True
        case "false" | "0" | "no":
            return False
        case _:
            msg = f"{provider}.{name} is {raw!r}, not true or false"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class UserAgent:
    """The self-identifying User-Agent a live test sends: a product token and, optionally, the operator's contact."""

    product: str
    contact: str = ""

    def normalized_contact(self) -> str:
        """Return the contact as a dereferenceable token, or ``""`` when unset: a bare address gains ``mailto:``."""
        raw = self.contact.strip()
        if not raw:
            return ""
        return raw if "://" in raw or raw.startswith("mailto:") else f"mailto:{raw}"

    def header(self) -> str:
        """``Product/Version (+contact)``, the contact clause dropped when unset."""
        contact = self.normalized_contact()
        return f"{self.product} (+{contact})" if contact else self.product


def user_agent(default_product: str) -> UserAgent:
    """``user_agent.product`` (else *default_product*) and ``user_agent.contact``; never skips, neither is required.

    The product token is in every request and is no secret; the contact is the operator's, so it is remembered for the
    scrub like a credential.
    """
    product = _value("user_agent", "product", secret=False) or default_product
    return UserAgent(product=product, contact=_value("user_agent", "contact") or "")
