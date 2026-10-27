# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""A client for lda.gov, the U.S. Senate's Lobbying Disclosure Act REST API (``https://lda.gov/api/v1/``), keyless.

One ``AsyncBaseClient`` for the one host, one method per documented read (the 18 ``GET``s of the API's OpenAPI
document, saved as ``docs_paths.json``). A list endpoint returns headgate's lazy ``Paginated`` walk (see
``pagination``); an item or constants endpoint returns its decoded body. Every method returns its decoded type or
raises a ``headgate.errors`` error; ``get_filing`` alone answers ``None``, for the measured ``404`` of an unknown uuid.

**Terms** (https://lda.gov/api/tos/, last modified 2019-08-22, read 2026-10-27). Automated use is allowed, keyed or
anonymous; anonymous use is limited to 15 requests a minute per originating IP address (a registered key: 120 a minute
per user), and a user the Senate believes has tried to exceed or circumvent the limits may be blocked. Anyone who uses
the data must cite the date it was retrieved and state that "Senate Office of Public Records cannot vouch for the data
or analyses derived from these data after the data have been retrieved from LDA.gov"; must not modify or falsely
represent content and still cite LDA.gov as the source; and must not use the U.S. Senate Seal. This client returns
values as sent, adds no attribution of its own and records no retrieval date: the code that stores or shows the data
does both. The ``Date`` header of each response gives the retrieval date (UTC).

**Pace: one request every 10 seconds**, which is 6 a minute: well under the anonymous limit, so the client never relies
on the server to slow it down. headgate's default retry policy (three attempts) re-sends a network failure, a ``5xx`` or
a ``429``, each attempt paced like any request. It waits a ``Retry-After`` of up to 30 seconds; the docs' example
``429`` carries ``Retry-After: 1596``, which is not waited: the call raises ``RateLimitError`` with that delay as its
``retry_after``, and the caller stops for as long as it says. The constants lists do not count against the limit (docs)
but are paced like the rest. The optional API key (``Authorization: Token <key>``) only raises the limit; this client
does not take one.

**Measured 2026-10-27** (30 requests in all, the terms, docs and spec pages included, at least 10 seconds apart, with
``User-Agent: headgate-client-skill-example/0.1 (+https://github.com/kelsayed17/headgate-client-skill)``, no key):

* All 18 documented reads answer ``200`` with ``Content-Type: application/json``. No response carried a rate-limit
  header, so the pace is this client's own.
* A list page is ``{"count", "next", "previous", "results"}``; ``next`` and ``previous`` are absolute ``https://lda.gov``
  URLs carrying the request's filters and the page number, ``null`` at either end. ``page_size`` defaults to 25, the
  most the docs allow.
* An empty result is ``200 {"count":0,"next":null,"previous":null,"results":[]}``.
* An unknown filing uuid is ``404 {"detail":"No Filing matches the given query."}``: ``get_filing`` returns ``None``.
* A filter value the API refuses is ``400`` naming the field: ``filing_year=1850`` gave ``{"filing_year":["Select a
  valid choice. 1850 is not one of the available choices."]}``. It raises ``UpstreamStatusError``.
* A page past the last is ``404 {"detail":"Invalid page."}``; a walk never asks for one, since it stops where ``next``
  is ``null``.
* ``/filings/?page=2`` with no filter is ``400 {"detail":"You must pass at least one query string parameter to filter
  the results and be able to paginate the results. See …"}``: walk filings and contribution reports with a filter.
* The OpenAPI document answers ``406 {"detail":"Could not satisfy the request Accept header."}`` to
  ``Accept: application/json``, and serves YAML to an OpenAPI ``Accept``.

**Not measured:** a ``429`` (provoking one would break the terms; the shape above is the docs' example), a ``401`` for a
bad key (no key was used; the docs give ``{"detail": "Invalid token."}``), a ``404`` for an unknown contribution report,
registrant, client or lobbyist id (those raise ``UpstreamStatusError`` until measured), and the keyed limit.
"""

from http import HTTPStatus
from typing import TYPE_CHECKING, Unpack

from headgate import AsyncBaseClient, Expect, HttpOptions, Rate, nothing
from headgate.msgspec import decoder

from examples.msgspec.lda.models import (
    Client,
    ClientsParams,
    Constant,
    ContributionReport,
    ContributionsParams,
    Filing,
    FilingsParams,
    GovernmentEntity,
    LobbyistsParams,
    LobbyistWithRegistrant,
    Page,
    Registrant,
    RegistrantsParams,
)
from examples.msgspec.lda.pagination import (
    CLIENT_PAGES,
    CONTRIBUTION_PAGES,
    FILING_PAGES,
    LOBBYIST_PAGES,
    PAGE_LIMIT,
    REGISTRANT_PAGES,
)

if TYPE_CHECKING:
    import httpx2
    from headgate import Paginated

BASE_URL = "https://lda.gov"
"""The API's host. Each path carries ``api/v1/``: a t-string hole is escaped as one path segment, so the prefix cannot
ride a hole, and the base URL carries no path."""

PACE = Rate.per_second(0.1)
"""One request every 10 seconds, with no burst: a rate below one a second still allows one request at a time."""

# Readers: built once, at import, where a bad declaration fails.
FILINGS = decoder(Page[Filing])
FILING = decoder(Filing)
FILING_OR_NONE = Expect(FILING).on(HTTPStatus.NOT_FOUND, nothing)  # an unknown uuid
CONTRIBUTIONS = decoder(Page[ContributionReport])
CONTRIBUTION = decoder(ContributionReport)
REGISTRANTS = decoder(Page[Registrant])
REGISTRANT = decoder(Registrant)
CLIENTS = decoder(Page[Client])
CLIENT = decoder(Client)
LOBBYISTS = decoder(Page[LobbyistWithRegistrant])
LOBBYIST = decoder(LobbyistWithRegistrant)
CONSTANTS = decoder(list[Constant])
GOVERNMENT_ENTITIES = decoder(list[GovernmentEntity])


class LdaClient(AsyncBaseClient):
    """Read lda.gov's filings, contribution reports, registrants, clients, lobbyists and constants lists."""

    def __init__(self, *, user_agent: str, transport: httpx2.AsyncBaseTransport | None = None) -> None:
        """Identify every request as ``user_agent``; ``transport`` replaces the network, as a test does."""
        super().__init__(
            base_url=BASE_URL,
            rate=PACE,
            http=HttpOptions(
                transport=transport,
                headers={"User-Agent": user_agent, "Accept": "application/json"},
            ),
        )

    def get_filings(self, **params: Unpack[FilingsParams]) -> Paginated[Page[Filing], Filing]:
        """Walk the LD-1 registrations and LD-2 reports that match ``params``, page by page as iterated."""
        return self.paginate("api/v1/filings/", params=params, expect=FILINGS, pages=FILING_PAGES, limit=PAGE_LIMIT)

    async def get_filing(self, filing_uuid: str) -> Filing | None:
        """Return the filing ``filing_uuid``, or ``None`` when there is none."""
        return await self.get(t"api/v1/filings/{filing_uuid}/", expect=FILING_OR_NONE)

    def get_contributions(
        self, **params: Unpack[ContributionsParams]
    ) -> Paginated[Page[ContributionReport], ContributionReport]:
        """Walk the LD-203 contribution reports that match ``params``, page by page as iterated."""
        return self.paginate(
            "api/v1/contributions/", params=params, expect=CONTRIBUTIONS, pages=CONTRIBUTION_PAGES, limit=PAGE_LIMIT
        )

    async def get_contribution(self, filing_uuid: str) -> ContributionReport:
        """Return the contribution report ``filing_uuid``."""
        return await self.get(t"api/v1/contributions/{filing_uuid}/", expect=CONTRIBUTION)

    def get_registrants(self, **params: Unpack[RegistrantsParams]) -> Paginated[Page[Registrant], Registrant]:
        """Walk the registrants that match ``params``, page by page as iterated."""
        return self.paginate(
            "api/v1/registrants/", params=params, expect=REGISTRANTS, pages=REGISTRANT_PAGES, limit=PAGE_LIMIT
        )

    async def get_registrant(self, registrant_id: int) -> Registrant:
        """Return the registrant ``registrant_id``."""
        return await self.get(t"api/v1/registrants/{registrant_id}/", expect=REGISTRANT)

    def get_clients(self, **params: Unpack[ClientsParams]) -> Paginated[Page[Client], Client]:
        """Walk the clients that match ``params``, each with its registrant, page by page as iterated."""
        return self.paginate("api/v1/clients/", params=params, expect=CLIENTS, pages=CLIENT_PAGES, limit=PAGE_LIMIT)

    async def get_client(self, client_id: int) -> Client:
        """Return the client ``client_id`` with its registrant."""
        return await self.get(t"api/v1/clients/{client_id}/", expect=CLIENT)

    def get_lobbyists(
        self, **params: Unpack[LobbyistsParams]
    ) -> Paginated[Page[LobbyistWithRegistrant], LobbyistWithRegistrant]:
        """Walk the lobbyists that match ``params``, each with its registrant, page by page as iterated."""
        return self.paginate(
            "api/v1/lobbyists/", params=params, expect=LOBBYISTS, pages=LOBBYIST_PAGES, limit=PAGE_LIMIT
        )

    async def get_lobbyist(self, lobbyist_id: int) -> LobbyistWithRegistrant:
        """Return the lobbyist ``lobbyist_id`` with their registrant."""
        return await self.get(t"api/v1/lobbyists/{lobbyist_id}/", expect=LOBBYIST)

    async def get_constants_filing_filingtypes(self) -> list[Constant]:
        """Return the filing types (``RR`` registration, ``Q1`` first-quarter report, …)."""
        return await self.get("api/v1/constants/filing/filingtypes/", expect=CONSTANTS)

    async def get_constants_filing_lobbyingactivityissues(self) -> list[Constant]:
        """Return the general lobbying issue codes (``ACC`` accounting, ``AGR`` agriculture, …)."""
        return await self.get("api/v1/constants/filing/lobbyingactivityissues/", expect=CONSTANTS)

    async def get_constants_filing_governmententities(self) -> list[GovernmentEntity]:
        """Return the government bodies a lobbying activity can name, keyed by ``id``."""
        return await self.get("api/v1/constants/filing/governmententities/", expect=GOVERNMENT_ENTITIES)

    async def get_constants_general_countries(self) -> list[Constant]:
        """Return the country codes."""
        return await self.get("api/v1/constants/general/countries/", expect=CONSTANTS)

    async def get_constants_general_states(self) -> list[Constant]:
        """Return the U.S. state codes."""
        return await self.get("api/v1/constants/general/states/", expect=CONSTANTS)

    async def get_constants_lobbyist_prefixes(self) -> list[Constant]:
        """Return the name prefixes a lobbyist may have (``dr``, ``mr``, …)."""
        return await self.get("api/v1/constants/lobbyist/prefixes/", expect=CONSTANTS)

    async def get_constants_lobbyist_suffixes(self) -> list[Constant]:
        """Return the name suffixes a lobbyist may have."""
        return await self.get("api/v1/constants/lobbyist/suffixes/", expect=CONSTANTS)

    async def get_constants_contribution_itemtypes(self) -> list[Constant]:
        """Return the contribution item types (``feca``, ``he`` honorary expenses, …)."""
        return await self.get("api/v1/constants/contribution/itemtypes/", expect=CONSTANTS)
