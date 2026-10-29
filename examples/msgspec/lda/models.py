# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""lda.gov's wire shapes: frozen ``msgspec.Struct``s with the API's own field names, and the list endpoints' params.

Modelled on the API's OpenAPI document (``https://lda.gov/api/openapi/v1/``, version 1.0.0, read 2026-10-27) and
checked against the bodies recorded the same day (``tests/fixtures/``). Where the two disagree, the wire wins:

* **Every field is present.** The docs say a blank field is sent as ``null``, never omitted, and every recorded body
  agrees, so no field has a default: a body that drops a field fails to decode instead of reading as ``None``.
* **Nullability is wider than the spec says.** The spec marks most text fields non-null, but the wire sends ``null``
  for some of them (``registrant_ppb_country`` and ``expenses_method_display`` on a filing, ``prefix_display`` and
  ``suffix_display`` on a lobbyist). Only the keys that identify a record (``id``, ``url``, ``name``, ``filing_uuid``,
  the filing's type, year and period, a constant's ``value``) are non-null here; every other scalar may be ``None``.
* **A client's ``client_id`` is an integer.** The spec types it as a string; the wire sends ``51370``.

Values decode to their types, unchanged: ``filing_uuid`` to ``UUID``, dates to ``date``, timestamps to ``datetime``
with the offset sent (``2025-08-07T16:33:53-04:00``), and money (``income``, ``expenses``, amounts and ownership
percentages) to ``Decimal`` from the string the spec types as ``format: decimal``.

**Not measured:** populated ``conviction_disclosures``, ``foreign_entities``, ``affiliated_organizations``, ``pacs``
and ``contribution_items`` (every recorded body had them empty), and a non-null ``income``. Their structs are the
spec's.
"""

import datetime as dt
from decimal import Decimal
from typing import Literal, TypedDict
from uuid import UUID

import msgspec

# Pages


class Page[T](msgspec.Struct, frozen=True, gc=False):
    """One page of a list endpoint: up to ``page_size`` rows (25 at most), and the absolute URLs of its neighbours.

    ``next`` is ``None`` on the last page, ``previous`` on the first. ``count`` is the whole result's size.
    """

    count: int
    next: str | None
    previous: str | None
    results: list[T]


# Registrants, clients and lobbyists


class Registrant(msgspec.Struct, frozen=True, gc=False):
    """A registrant: a lobbying firm, or an organisation that lobbies for itself. Also nested in other records."""

    id: int
    url: str
    house_registrant_id: int | None
    name: str
    description: str | None
    address_1: str | None
    address_2: str | None
    address_3: str | None
    address_4: str | None
    city: str | None
    state: str | None
    state_display: str | None
    zip: str | None
    country: str | None
    country_display: str | None
    ppb_country: str | None
    ppb_country_display: str | None
    contact_name: str | None
    contact_telephone: str | None
    dt_updated: dt.datetime | None


class FilingClient(msgspec.Struct, frozen=True, gc=False):
    """A client as a filing names it: the organisation the registrant lobbies for, without its registrant."""

    id: int
    url: str
    client_id: int
    name: str
    general_description: str | None
    client_government_entity: bool | None
    client_self_select: bool | None
    state: str | None
    state_display: str | None
    country: str | None
    country_display: str | None
    ppb_state: str | None
    ppb_state_display: str | None
    ppb_country: str | None
    ppb_country_display: str | None
    effective_date: dt.date | None


class Client(FilingClient, frozen=True):
    """A client as ``/clients/`` returns it: a filing's client plus the registrant that lobbies for it."""

    registrant: Registrant


class Lobbyist(msgspec.Struct, frozen=True, gc=False):
    """A lobbyist as a filing or a contribution report names one, without the registrant."""

    id: int
    prefix: str | None
    prefix_display: str | None
    first_name: str | None
    nickname: str | None
    middle_name: str | None
    last_name: str | None
    suffix: str | None
    suffix_display: str | None


class LobbyistWithRegistrant(Lobbyist, frozen=True):
    """A lobbyist as ``/lobbyists/`` returns one: plus the registrant that employs them (the spec's own name)."""

    registrant: Registrant


# Filings (LD-1 registrations and LD-2 reports)


class GovernmentEntity(msgspec.Struct, frozen=True, gc=False):
    """A House, Senate or agency body: in a lobbying activity, and as a row of the government entities constants."""

    id: int
    name: str


class ActivityLobbyist(msgspec.Struct, frozen=True, gc=False):
    """A lobbyist on one lobbying activity, with the covered government position they disclosed, if any."""

    lobbyist: Lobbyist
    covered_position: str | None
    new: bool | None


class LobbyingActivity(msgspec.Struct, frozen=True, gc=False):
    """One issue area of a filing. On filings posted before 2021-02-14 the entities are the whole filing's (docs)."""

    general_issue_code: str
    general_issue_code_display: str | None
    description: str | None
    foreign_entity_issues: str | None
    lobbyists: list[ActivityLobbyist]
    government_entities: list[GovernmentEntity]


class ConvictionDisclosure(msgspec.Struct, frozen=True, gc=False):
    """A lobbyist's disclosed conviction."""

    lobbyist: Lobbyist
    date: dt.date | None
    description: str | None


class ForeignEntity(msgspec.Struct, frozen=True, gc=False):
    """A foreign entity with an interest in the client."""

    name: str
    contribution: Decimal | None
    ownership_percentage: Decimal | None
    address: str | None
    city: str | None
    state: str | None
    state_display: str | None
    country: str | None
    country_display: str | None
    ppb_city: str | None
    ppb_state: str | None
    ppb_state_display: str | None
    ppb_country: str | None
    ppb_country_display: str | None


class AffiliatedOrganization(msgspec.Struct, frozen=True, gc=False):
    """An organisation affiliated with the client."""

    name: str
    url: str | None
    address_1: str | None
    address_2: str | None
    address_3: str | None
    address_4: str | None
    city: str | None
    state: str | None
    state_display: str | None
    zip: str | None
    country: str | None
    country_display: str | None
    ppb_city: str | None
    ppb_state: str | None
    ppb_state_display: str | None
    ppb_country: str | None
    ppb_country_display: str | None


class Filing(msgspec.Struct, frozen=True, gc=False):
    """One LD-1 registration or LD-2 report, or an amendment or termination of one.

    ``income`` (a firm lobbying for a client) or ``expenses`` (an organisation lobbying for itself) is the period's
    reported amount; both are ``None`` on a registration and on a report of no activity. ``filing_document_url`` is the
    filed document itself (HTML or PDF), which this client does not fetch.
    """

    url: str
    filing_uuid: UUID
    filing_type: str
    filing_type_display: str | None
    filing_year: int
    filing_period: str
    filing_period_display: str | None
    filing_document_url: str | None
    filing_document_content_type: str | None
    income: Decimal | None
    expenses: Decimal | None
    expenses_method: str | None
    expenses_method_display: str | None
    posted_by_name: str | None
    dt_posted: dt.datetime | None
    termination_date: dt.date | None
    registrant_country: str | None
    registrant_ppb_country: str | None
    registrant_address_1: str | None
    registrant_address_2: str | None
    registrant_different_address: bool | None
    registrant_city: str | None
    registrant_state: str | None
    registrant_zip: str | None
    registrant: Registrant
    client: FilingClient
    lobbying_activities: list[LobbyingActivity]
    conviction_disclosures: list[ConvictionDisclosure]
    foreign_entities: list[ForeignEntity]
    affiliated_organizations: list[AffiliatedOrganization]


# Contribution reports (LD-203)


class ContributionItem(msgspec.Struct, frozen=True, gc=False):
    """One reported contribution."""

    contribution_type: str
    contribution_type_display: str | None
    contributor_name: str | None
    payee_name: str | None
    honoree_name: str | None
    amount: Decimal | None
    date: dt.date | None


class ContributionReport(msgspec.Struct, frozen=True, gc=False):
    """One LD-203 report: the contributions a registrant or one of its lobbyists reported for a half year.

    ``lobbyist`` names the lobbyist on a lobbyist's report (both recorded reports were one); the spec lets it be
    ``None``. ``no_contributions`` is ``True`` when the filer reported none.
    """

    url: str
    filing_uuid: UUID
    filing_type: str
    filing_type_display: str | None
    filing_year: int
    filing_period: str
    filing_period_display: str | None
    filing_document_url: str | None
    filing_document_content_type: str | None
    filer_type: str | None
    filer_type_display: str | None
    dt_posted: dt.datetime | None
    contact_name: str | None
    comments: str | None
    address_1: str | None
    address_2: str | None
    city: str | None
    state: str | None
    state_display: str | None
    zip: str | None
    country: str | None
    country_display: str | None
    registrant: Registrant
    lobbyist: Lobbyist | None
    no_contributions: bool | None
    pacs: list[str]
    contribution_items: list[ContributionItem]


# Constants


class Constant(msgspec.Struct, frozen=True, gc=False):
    """A ``{value, name}`` constant: a filing type, issue code, country, state, prefix, suffix or item type."""

    value: str
    name: str


# Query parameters

type FilingPeriod = Literal[
    "first_quarter", "second_quarter", "third_quarter", "fourth_quarter", "mid_year", "year_end"
]
"""The ``filing_period`` values the spec lists, which are also the wire values of ``Filing.filing_period``."""


class PageParams(TypedDict, total=False):
    """The paging and ordering params of every list endpoint.

    The client's walk sets ``page`` itself from each page's ``next`` URL; a caller passes it only to start further in.
    ``page_size`` is at most 25. ``ordering`` names a field, ``-`` first for descending.
    """

    page: int
    page_size: int
    ordering: str


class FilingsParams(PageParams, total=False):
    """Filters of ``GET /api/v1/filings/``. Dates are ``yyyy-mm-dd``; the text filters take the docs' search syntax.

    A page past the first needs a filter besides paging (``filing_year`` is the docs' advice), or it is a ``400``.
    """

    filing_uuid: str
    registrant_id: int
    registrant_name: str
    registrant_country: str
    registrant_ppb_country: str
    client_id: int
    client_name: str
    client_state: str
    client_country: str
    client_ppb_state: str
    client_ppb_country: str
    lobbyist_id: int
    lobbyist_name: str
    lobbyist_covered_position: str
    lobbyist_covered_position_indicator: bool
    lobbyist_conviction_disclosure: str
    lobbyist_conviction_disclosure_indicator: bool
    lobbyist_conviction_date_range_after: str
    lobbyist_conviction_date_range_before: str
    filing_type: str
    filing_year: int
    filing_period: FilingPeriod
    filing_dt_posted_after: str
    filing_dt_posted_before: str
    filing_amount_reported_min: str
    filing_amount_reported_max: str
    filing_specific_lobbying_issues: str
    affiliated_organization_name: str
    affiliated_organization_country: str
    affiliated_organization_listed_indicator: bool
    foreign_entity_name: str
    foreign_entity_country: str
    foreign_entity_listed_indicator: bool
    foreign_entity_ppb_country: str
    foreign_entity_ownership_percentage_min: str
    foreign_entity_ownership_percentage_max: str


class ContributionsParams(PageParams, total=False):
    """Filters of ``GET /api/v1/contributions/``. As with filings, a page past the first needs a filter."""

    filing_uuid: str
    filing_type: str
    filing_year: int
    filing_period: FilingPeriod
    filing_dt_posted_after: str
    filing_dt_posted_before: str
    registrant_id: int
    registrant_name: str
    lobbyist_id: int
    lobbyist_name: str
    lobbyist_exclude: bool
    contribution_date_after: str
    contribution_date_before: str
    contribution_amount_min: str
    contribution_amount_max: str
    contribution_type: str
    contribution_contributor: str
    contribution_payee: str
    contribution_honoree: str


class RegistrantsParams(PageParams, total=False):
    """Filters of ``GET /api/v1/registrants/``."""

    id: int
    registrant_name: str
    state: str
    country: str
    ppb_country: str
    dt_updated_after: str
    dt_updated_before: str


class ClientsParams(PageParams, total=False):
    """Filters of ``GET /api/v1/clients/``."""

    id: int
    client_name: str
    client_state: str
    client_country: str
    client_ppb_state: str
    client_ppb_country: str
    registrant_id: int
    registrant_name: str


class LobbyistsParams(PageParams, total=False):
    """Filters of ``GET /api/v1/lobbyists/``."""

    id: int
    lobbyist_name: str
    registrant_id: int
    registrant_name: str
