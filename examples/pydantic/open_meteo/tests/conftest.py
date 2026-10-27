# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""Fixtures for the Open-Meteo tests: a fake network, both clients on it, and snapshots that read like the wire."""

from typing import TYPE_CHECKING, NamedTuple, override

import pytest
from headgate.pydantic import to_builtins
from headgate.testing import FakeTransport, TestClock, isolated_breakers
from syrupy.extensions.json import JSONSnapshotExtension

from examples.pydantic.open_meteo.client import ArchiveClient, ForecastClient

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable

    from syrupy.assertion import SnapshotAssertion

USER_AGENT = "headgate-client-skill-tests/0.1 (+https://github.com/kelsayed17/headgate-client-skill)"
"""The User-Agent the tests build the clients with, and assert they send."""


class ModelSnapshot(JSONSnapshotExtension):
    """syrupy's JSON snapshot of a decoded value, its models written out as the JSON objects their fields hold."""

    @override
    def serialize(
        self,
        data: object,
        *,
        exclude: Callable[..., bool] | None = None,
        include: Callable[..., bool] | None = None,
        matcher: Callable[..., object] | None = None,
    ) -> str | bytes:
        """Return the snapshot of ``data`` after ``headgate.pydantic.to_builtins``, each series' variables included."""
        return super().serialize(to_builtins(data), exclude=exclude, include=include, matcher=matcher)


class Clients(NamedTuple):
    """One client per Open-Meteo host, both on the same fake network and clock."""

    forecast: ForecastClient
    archive: ArchiveClient


@pytest.fixture
def snapshot(snapshot: SnapshotAssertion) -> SnapshotAssertion:
    """Return syrupy's snapshot, comparing decoded models as JSON files under ``__snapshots__/``."""
    return snapshot.use_extension(ModelSnapshot)


@pytest.fixture
def fake() -> FakeTransport:
    """Return an empty fake network; each test adds the routes it serves.

    A route matches the method and path only, never the host: ``/v1/forecast`` and ``/v1/archive`` differ, and each
    test asserts the full URL sent, so a client that called the other host would fail.
    """
    return FakeTransport()


@pytest.fixture
def clock() -> TestClock:
    """Return a clock that moves only when a client sleeps on it."""
    return TestClock()


@pytest.fixture
async def clients(fake: FakeTransport, clock: TestClock) -> AsyncIterator[Clients]:
    """Yield both clients on ``fake`` and ``clock``, with breakers of their own.

    Each client paces itself at one request every 2 seconds. On ``clock`` each wait advances the clock instead of
    taking time, so the pace holds (and is asserted) while the test runs at once; retries wait on it too.
    """
    with clock.install(), isolated_breakers():
        async with (
            ForecastClient(user_agent=USER_AGENT, transport=fake) as forecast,
            ArchiveClient(user_agent=USER_AGENT, transport=fake) as archive,
        ):
            yield Clients(forecast, archive)
