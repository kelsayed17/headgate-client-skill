# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""Offline tests of ``LdaClient`` through its real headgate stack.

Every body served here was recorded from lda.gov on 2026-10-27 (see the client's module docstring), with lists trimmed
to two rows and a registrant's contact person and telephone, and a contribution report filer's street address and ZIP,
replaced by ``REDACTED``. Each decode test asserts the request the client sent (host, path and query) and the decoded
value, against a syrupy snapshot under ``__snapshots__/``.
"""

import json
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple
from urllib.parse import urlsplit

import httpx2
import pytest
from headgate import PageLimitError, UpstreamStatusError

from examples.msgspec.lda.pagination import MAX_PAGES
from examples.msgspec.lda.tests.conftest import USER_AGENT

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from headgate import Paginated
    from headgate.testing import FakeTransport, TestClock
    from syrupy.assertion import SnapshotAssertion

    from examples.msgspec.lda.client import LdaClient

pytestmark = pytest.mark.anyio

FIXTURES = Path(__file__).parent / "fixtures"
FILING_UUID = "6b613d78-b468-4ac6-b0d5-6926627fb136"
CONTRIBUTION_UUID = "082b5ec0-e293-4bbe-9ee0-62ce64171941"
REGISTRANT_ID = 401104718
CLIENT_ID = 51370
LOBBYIST_ID = 67392
API = "https://lda.gov/api/v1"


def recorded(fixture: str, status: int = 200) -> httpx2.Response:
    """Return the recorded body ``fixture`` as lda.gov sent it: JSON, with ``status``."""
    return httpx2.Response(
        status, content=(FIXTURES / fixture).read_bytes(), headers={"Content-Type": "application/json"}
    )


async def first_page[P, I](walk: Paginated[P, I]) -> P:
    """Return the first page of ``walk``, fetching no other."""
    async for page in walk.pages():
        return page
    msg = "the walk yielded no page"
    raise AssertionError(msg)


class Case(NamedTuple):
    """A documented read: its fixture's name (also the test id), the call, and the URL the client must send."""

    fixture: str
    read: Callable[[LdaClient], Awaitable[object]]
    url: str


READS = [
    Case(
        "filings",
        lambda lda: first_page(lda.get_filings(filing_year=2025, filing_type="Q3", page_size=2)),
        f"{API}/filings/?filing_year=2025&filing_type=Q3&page_size=2",
    ),
    Case("filing", lambda lda: lda.get_filing(FILING_UUID), f"{API}/filings/{FILING_UUID}/"),
    Case(
        "contributions",
        lambda lda: first_page(lda.get_contributions(filing_year=2025, filing_period="mid_year", page_size=2)),
        f"{API}/contributions/?filing_year=2025&filing_period=mid_year&page_size=2",
    ),
    Case(
        "contribution", lambda lda: lda.get_contribution(CONTRIBUTION_UUID), f"{API}/contributions/{CONTRIBUTION_UUID}/"
    ),
    Case(
        "registrants",
        lambda lda: first_page(lda.get_registrants(registrant_name="strategies", state="DC", page_size=2)),
        f"{API}/registrants/?registrant_name=strategies&state=DC&page_size=2",
    ),
    Case("registrant", lambda lda: lda.get_registrant(REGISTRANT_ID), f"{API}/registrants/{REGISTRANT_ID}/"),
    Case(
        "clients",
        lambda lda: first_page(lda.get_clients(registrant_id=REGISTRANT_ID, page_size=2)),
        f"{API}/clients/?registrant_id={REGISTRANT_ID}&page_size=2",
    ),
    Case("client", lambda lda: lda.get_client(CLIENT_ID), f"{API}/clients/{CLIENT_ID}/"),
    Case(
        "lobbyists",
        lambda lda: first_page(lda.get_lobbyists(registrant_id=REGISTRANT_ID, page_size=2)),
        f"{API}/lobbyists/?registrant_id={REGISTRANT_ID}&page_size=2",
    ),
    Case("lobbyist", lambda lda: lda.get_lobbyist(LOBBYIST_ID), f"{API}/lobbyists/{LOBBYIST_ID}/"),
    Case(
        "constants_filing_filingtypes",
        lambda lda: lda.get_constants_filing_filingtypes(),
        f"{API}/constants/filing/filingtypes/",
    ),
    Case(
        "constants_filing_lobbyingactivityissues",
        lambda lda: lda.get_constants_filing_lobbyingactivityissues(),
        f"{API}/constants/filing/lobbyingactivityissues/",
    ),
    Case(
        "constants_filing_governmententities",
        lambda lda: lda.get_constants_filing_governmententities(),
        f"{API}/constants/filing/governmententities/",
    ),
    Case(
        "constants_general_countries",
        lambda lda: lda.get_constants_general_countries(),
        f"{API}/constants/general/countries/",
    ),
    Case(
        "constants_general_states", lambda lda: lda.get_constants_general_states(), f"{API}/constants/general/states/"
    ),
    Case(
        "constants_lobbyist_prefixes",
        lambda lda: lda.get_constants_lobbyist_prefixes(),
        f"{API}/constants/lobbyist/prefixes/",
    ),
    Case(
        "constants_lobbyist_suffixes",
        lambda lda: lda.get_constants_lobbyist_suffixes(),
        f"{API}/constants/lobbyist/suffixes/",
    ),
    Case(
        "constants_contribution_itemtypes",
        lambda lda: lda.get_constants_contribution_itemtypes(),
        f"{API}/constants/contribution/itemtypes/",
    ),
]
"""Every documented read, each served its recorded body."""


@pytest.mark.parametrize("case", READS, ids=[case.fixture for case in READS])
async def test_read_decodes(lda: LdaClient, fake: FakeTransport, snapshot: SnapshotAssertion, case: Case) -> None:
    """The recorded body decodes to the snapshot, from one GET of exactly the documented URL."""
    fake.reply("GET", urlsplit(case.url).path, recorded(f"{case.fixture}.json"))

    decoded = await case.read(lda)

    assert [str(request.url) for request in fake.calls] == [case.url]
    assert decoded == snapshot


async def test_sends_its_user_agent(lda: LdaClient, fake: FakeTransport) -> None:
    """Every request names the caller's User-Agent and asks for JSON."""
    fake.reply("GET", "/api/v1/constants/general/states/", recorded("constants_general_states.json"))

    await lda.get_constants_general_states()

    (request,) = fake.calls
    assert request.headers["User-Agent"] == USER_AGENT
    assert request.headers["Accept"] == "application/json"


async def test_paces_one_request_every_10_seconds(lda: LdaClient, fake: FakeTransport, clock: TestClock) -> None:
    """The second of two back-to-back calls waits 10 seconds for its turn: there is no burst."""
    fake.reply("GET", "/api/v1/constants/general/states/", recorded("constants_general_states.json"))

    await lda.get_constants_general_states()
    await lda.get_constants_general_states()

    assert len(fake.calls) == 2  # noqa: PLR2004 -- the two calls made
    assert clock.now == pytest.approx(10.0)


async def test_unknown_filing_is_none(lda: LdaClient, fake: FakeTransport) -> None:
    """An unknown uuid is the documented 404, which the client reads as ``None``."""
    missing = "00000000-0000-0000-0000-000000000000"
    fake.reply("GET", f"/api/v1/filings/{missing}/", recorded("filing_not_found.json", 404))

    assert await lda.get_filing(missing) is None


async def test_bad_filter_raises_upstream_status_error(lda: LdaClient, fake: FakeTransport) -> None:
    """A filter value the API refuses is its recorded 400, raised once, with the API's reason in the message."""
    fake.reply("GET", "/api/v1/filings/", recorded("filings_bad_year.json", 400))

    with pytest.raises(UpstreamStatusError) as raised:
        await lda.get_filings(filing_year=1850).collect()

    assert raised.value.status_code == 400  # noqa: PLR2004 -- the status lda.gov sent
    assert "1850 is not one of the available choices" in str(raised.value)
    assert len(fake.calls) == 1


async def test_empty_result_is_an_empty_walk(lda: LdaClient, fake: FakeTransport) -> None:
    """A filter that matches nothing is a 200 page with no rows: the walk yields nothing after one request."""
    fake.reply("GET", "/api/v1/filings/", recorded("filings_empty.json"))

    assert await lda.get_filings(filing_year=2025, registrant_name="zzqqxxnonexistent").collect() == []
    assert len(fake.calls) == 1


async def test_walk_follows_the_next_url(lda: LdaClient, fake: FakeTransport, snapshot: SnapshotAssertion) -> None:
    """A walk sends the caller's query first, then the ``next`` URL each page names, and stops where it is null."""
    fake.reply(
        "GET", "/api/v1/lobbyists/", recorded("lobbyists_walk_page_1.json"), recorded("lobbyists_walk_page_2.json")
    )

    rows = await lda.get_lobbyists(registrant_id=REGISTRANT_ID, page_size=16).collect()

    assert [str(request.url) for request in fake.calls] == [
        f"{API}/lobbyists/?registrant_id={REGISTRANT_ID}&page_size=16",
        f"{API}/lobbyists/?page=2&page_size=16&registrant_id={REGISTRANT_ID}",
    ]
    assert rows == snapshot


async def test_walk_stops_at_page_limit(lda: LdaClient, fake: FakeTransport) -> None:
    """A walk that keeps naming a next page raises ``PageLimitError`` after ``MAX_PAGES`` requests, never more."""
    page = json.loads((FIXTURES / "lobbyists_walk_page_1.json").read_bytes())

    def endless(request: httpx2.Request) -> httpx2.Response:
        number = int(request.url.params.get("page", "1"))
        return httpx2.Response(200, json={**page, "next": f"{API}/lobbyists/?page={number + 1}&page_size=2"})

    fake.reply("GET", "/api/v1/lobbyists/", endless)

    with pytest.raises(PageLimitError) as raised:
        await lda.get_lobbyists(page_size=2).collect()

    assert raised.value.pages == MAX_PAGES
    assert len(fake.calls) == MAX_PAGES
