# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""Offline tests of ``ForecastClient`` and ``ArchiveClient`` through their real headgate stack.

Every body served here but the 429 was recorded from Open-Meteo on 2026-10-27 (see the client's module docstring), with
each series trimmed to its first four values; nothing else is changed. The bodies carry no personal data: the
coordinates asked for are central Berlin's, and the API answers with its grid cell's. Each decode test asserts the
request the client sent (host, path and query) and the decoded value, against a syrupy snapshot under
``__snapshots__/``.
"""

from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

import httpx2
import pytest
from headgate import RateLimitError, UpstreamStatusError

from examples.pydantic.open_meteo.client import PACE, free_api_budget
from examples.pydantic.open_meteo.tests.conftest import USER_AGENT

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from headgate.testing import FakeTransport, TestClock
    from syrupy.assertion import SnapshotAssertion

    from examples.pydantic.open_meteo.tests.conftest import Clients

pytestmark = pytest.mark.anyio

FIXTURES = Path(__file__).parent / "fixtures"
FORECAST = "https://api.open-meteo.com/v1/forecast"
ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"


def recorded(fixture: str, status: int = 200) -> httpx2.Response:
    """Return the recorded body ``fixture`` as Open-Meteo sent it: JSON, with ``status``."""
    return httpx2.Response(
        status, content=(FIXTURES / fixture).read_bytes(), headers={"Content-Type": "application/json; charset=utf-8"}
    )


def throttled() -> httpx2.Response:
    """Return the free API's quota 429, with a ``Retry-After`` of 42 seconds.

    Not recorded: provoking a 429 would break the terms. Status, headers and body are the example in Open-Meteo's own
    docs (https://github.com/open-meteo/open-meteo/blob/aeab72e33f6a30f1a87d1b5444fd169d536ce914/docs/api-rate-limiting.md,
    "When a limit is reached"); one limiter, per IP address, serves both hosts.
    """
    return httpx2.Response(
        429,
        json={"error": True, "reason": "Minutely API request limit exceeded. Please try again in one minute."},
        headers={
            "X-RateLimit-Limit": "600.0",
            "X-RateLimit-Remaining": "0.0",
            "X-RateLimit-Window": "60",
            "X-RateLimit-Reset": "1800000060",
            "Retry-After": "42",
        },
    )


class Case(NamedTuple):
    """A recorded read: its fixture's name (also the test id), the call, and the URL the client must send."""

    fixture: str
    read: Callable[[Clients], Awaitable[object]]
    url: str


READS = [
    Case(
        "forecast",
        lambda om: om.forecast.get_forecast(
            latitude=52.52,
            longitude=13.41,
            current="temperature_2m,weather_code",
            minutely_15="temperature_2m",
            hourly="temperature_2m,precipitation_probability",
            daily="temperature_2m_max,sunrise",
            timezone="Europe/Berlin",
            forecast_days=1,
        ),
        f"{FORECAST}?latitude=52.52&longitude=13.41&current=temperature_2m%2Cweather_code&minutely_15=temperature_2m"
        "&hourly=temperature_2m%2Cprecipitation_probability&daily=temperature_2m_max%2Csunrise&timezone=Europe%2FBerlin"
        "&forecast_days=1",
    ),
    Case(
        "forecast_unixtime",
        lambda om: om.forecast.get_forecast(
            latitude=52.52,
            longitude=13.41,
            hourly="temperature_2m",
            daily="sunrise",
            timeformat="unixtime",
            forecast_hours=3,
            forecast_days=1,
        ),
        f"{FORECAST}?latitude=52.52&longitude=13.41&hourly=temperature_2m&daily=sunrise&timeformat=unixtime"
        "&forecast_hours=3&forecast_days=1",
    ),
    Case(
        "archive",
        lambda om: om.archive.get_archive(
            latitude=52.52,
            longitude=13.41,
            start_date="2026-10-19",
            end_date="2026-10-26",
            hourly="temperature_2m",
            daily="temperature_2m_max,sunrise",
            timezone="Europe/Berlin",
        ),
        f"{ARCHIVE}?latitude=52.52&longitude=13.41&start_date=2026-10-19&end_date=2026-10-26&hourly=temperature_2m"
        "&daily=temperature_2m_max%2Csunrise&timezone=Europe%2FBerlin",
    ),
]
"""Every recorded read: the forecast with each block, the forecast in Unix time, and the archive."""


class Host(NamedTuple):
    """One of the two hosts: its name (the test id), its documented path, and a minimal read on its client."""

    name: str
    path: str
    read: Callable[[Clients], Awaitable[object]]


HOSTS = [
    Host(
        "forecast",
        "/v1/forecast",
        lambda om: om.forecast.get_forecast(latitude=52.52, longitude=13.41, hourly="temperature_2m"),
    ),
    Host(
        "archive",
        "/v1/archive",
        lambda om: om.archive.get_archive(
            latitude=52.52, longitude=13.41, start_date="2026-10-01", end_date="2026-10-02", hourly="temperature_2m"
        ),
    ),
]
"""Each host, for the tests both clients must pass."""


@pytest.mark.parametrize("case", READS, ids=[case.fixture for case in READS])
async def test_read_decodes(clients: Clients, fake: FakeTransport, snapshot: SnapshotAssertion, case: Case) -> None:
    """The recorded body decodes to the snapshot, from one GET of exactly the documented URL on the client's host."""
    fake.reply("GET", httpx2.URL(case.url).path, recorded(f"{case.fixture}.json"))

    decoded = await case.read(clients)

    assert [str(request.url) for request in fake.calls] == [case.url]
    assert decoded == snapshot


@pytest.mark.parametrize("host", HOSTS, ids=[host.name for host in HOSTS])
async def test_sends_its_user_agent(clients: Clients, fake: FakeTransport, host: Host) -> None:
    """Every request names the caller's product first, headgate's own tokens after it, and asks for JSON."""
    fake.reply("GET", host.path, recorded(f"{host.name}.json"))

    await host.read(clients)

    (request,) = fake.calls
    assert request.headers["User-Agent"].startswith(f"{USER_AGENT} headgate/")
    assert request.headers["Accept"] == "application/json"


def test_free_api_budget_is_the_documented_limits() -> None:
    """The production budget paces at ``PACE`` and lets at most five requests be in flight, Open-Meteo's queue limit."""
    budget = free_api_budget()

    assert budget.rate == PACE
    assert budget.max_in_flight == 5  # noqa: PLR2004 -- the free API's documented concurrency limit


async def test_paces_one_request_a_second(clients: Clients, fake: FakeTransport, clock: TestClock) -> None:
    """The second of two back-to-back calls on one client waits a second for its turn: there is no burst."""
    fake.reply("GET", "/v1/forecast", recorded("forecast.json"))

    await clients.forecast.get_forecast(latitude=52.52, longitude=13.41)
    await clients.forecast.get_forecast(latitude=52.52, longitude=13.41)

    assert len(fake.calls) == 2  # noqa: PLR2004 -- the two calls made
    assert clock.now == pytest.approx(1.0)


async def test_both_clients_share_one_pace(clients: Clients, fake: FakeTransport, clock: TestClock) -> None:
    """A call on one client waits for the other client's turn: the two hosts spend from one per-IP budget."""
    fake.reply("GET", "/v1/forecast", recorded("forecast.json"))
    fake.reply("GET", "/v1/archive", recorded("archive.json"))

    await clients.forecast.get_forecast(latitude=52.52, longitude=13.41)
    await clients.archive.get_archive(latitude=52.52, longitude=13.41, start_date="2026-10-19", end_date="2026-10-26")

    assert len(fake.calls) == 2  # noqa: PLR2004 -- the two calls made
    assert clock.now == pytest.approx(1.0)


async def test_throttle_on_one_host_pauses_the_other(clients: Clients, fake: FakeTransport, clock: TestClock) -> None:
    """A 429 from the forecast host pauses the archive client too: its next call waits out the ``Retry-After``."""
    fake.reply("GET", "/v1/forecast", throttled())
    fake.reply("GET", "/v1/archive", recorded("archive.json"))

    with pytest.raises(RateLimitError):
        await clients.forecast.get_forecast(latitude=52.52, longitude=13.41)
    await clients.archive.get_archive(latitude=52.52, longitude=13.41, start_date="2026-10-19", end_date="2026-10-26")

    assert [request.url.host for request in fake.calls] == ["api.open-meteo.com", "archive-api.open-meteo.com"]
    assert clock.now == pytest.approx(42.0)  # the 429's Retry-After, waited by the other host's call


@pytest.mark.parametrize("host", HOSTS, ids=[host.name for host in HOSTS])
async def test_bad_coordinate_raises_upstream_status_error(clients: Clients, fake: FakeTransport, host: Host) -> None:
    """A coordinate out of range is the host's recorded 400, raised once, with the API's reason in the message."""
    fake.reply("GET", host.path, recorded(f"{host.name}_bad_latitude.json", 400))

    with pytest.raises(UpstreamStatusError) as raised:
        await host.read(clients)

    assert raised.value.status_code == 400  # noqa: PLR2004 -- the status Open-Meteo sent
    assert "Latitude must be in range of -90 to 90°. Given: 91.0." in str(raised.value)
    assert len(fake.calls) == 1


@pytest.mark.parametrize("host", HOSTS, ids=[host.name for host in HOSTS])
async def test_throttle_raises_rate_limit_error(
    clients: Clients, fake: FakeTransport, clock: TestClock, host: Host
) -> None:
    """A 429 whose ``Retry-After`` is past what a retry waits raises at once, carrying the delay, and is not re-sent."""
    fake.reply("GET", host.path, throttled())

    with pytest.raises(RateLimitError) as raised:
        await host.read(clients)

    assert raised.value.retry_after == 42  # noqa: PLR2004 -- the docs' Retry-After
    assert len(fake.calls) == 1
    assert clock.now == 0
