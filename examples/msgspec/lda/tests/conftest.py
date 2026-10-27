# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""Fixtures for the lda.gov tests: a fake network, a client built on it, and snapshots that read like the wire."""

from typing import TYPE_CHECKING, override

import msgspec
import pytest
from headgate.testing import FakeTransport, TestClock, isolated_breakers
from syrupy.extensions.json import JSONSnapshotExtension

from examples.msgspec.lda.client import LdaClient

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable

    from syrupy.assertion import SnapshotAssertion

USER_AGENT = "headgate-client-skill-tests/0.1 (+https://github.com/kelsayed17/headgate-client-skill)"
"""The User-Agent the tests build the client with, and assert it sends."""


class StructSnapshot(JSONSnapshotExtension):
    """syrupy's JSON snapshot of a decoded value, its structs written out as the JSON objects their fields hold."""

    @override
    def serialize(
        self,
        data: object,
        *,
        exclude: Callable[..., bool] | None = None,
        include: Callable[..., bool] | None = None,
        matcher: Callable[..., object] | None = None,
    ) -> str | bytes:
        """Return the snapshot of ``data`` after ``msgspec.to_builtins``: dates, decimals and UUIDs as strings."""
        return super().serialize(msgspec.to_builtins(data), exclude=exclude, include=include, matcher=matcher)


@pytest.fixture
def snapshot(snapshot: SnapshotAssertion) -> SnapshotAssertion:
    """Return syrupy's snapshot, comparing decoded structs as JSON files under ``__snapshots__/``."""
    return snapshot.use_extension(StructSnapshot)


@pytest.fixture
def fake() -> FakeTransport:
    """Return an empty fake network; each test adds the routes it serves."""
    return FakeTransport()


@pytest.fixture
def clock() -> TestClock:
    """Return a clock that moves only when the client sleeps on it."""
    return TestClock()


@pytest.fixture
async def lda(fake: FakeTransport, clock: TestClock) -> AsyncIterator[LdaClient]:
    """Yield a client on ``fake`` and ``clock``, with breakers of its own.

    The client paces itself at one request every 10 seconds, so its waits are real: ``instant_retries()`` would skip
    them on the wall clock, and a long walk would then find its turn past the call's deadline. On ``clock`` each wait
    advances the clock instead, so the pace holds (and is asserted) while the test takes no time. Retries wait on it
    too.
    """
    with clock.install(), isolated_breakers():
        async with LdaClient(user_agent=USER_AGENT, transport=fake) as client:
            yield client
