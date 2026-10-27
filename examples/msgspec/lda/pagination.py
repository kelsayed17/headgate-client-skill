# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""How lda.gov's list endpoints page: headgate's ``NextUrl`` pager over each page's ``next``, within a page budget.

Each list page carries ``next``, the absolute URL of the page after it, with the caller's filters and the next
``page`` number (``https://lda.gov/api/v1/lobbyists/?page=2&page_size=16&registrant_id=401104718``, measured
2026-10-27), and ``null`` on the last page. ``NextUrl`` follows it as sent, so a walk is the API's own paging; headgate
resolves it against the URL that answered, sends it through the client's whole stack (pace, retries, breaker), and
raises ``ClientError`` if a page leads back to one already fetched. A walk also ends at a page with no rows.

**The page budget.** The client paces itself at one request every 10 seconds, so a walk costs that long per page: 200
pages of 25 rows take about 33 minutes. ``PAGE_LIMIT`` stops a walk at ``MAX_PAGES`` and raises ``PageLimitError``
(headgate's default ``on_limit="raise"``) when more pages remain, so a caller never mistakes a cut-short walk for the
whole result. A wider read is narrowed by filters instead: the third-quarter reports of 2025 alone are 21,120 filings
(``count``, measured 2026-10-27), 845 pages and more than two hours at the pace.
"""

from headgate import NextUrl, PageLimit

from examples.msgspec.lda.models import (
    Client,
    ContributionReport,
    Filing,
    LobbyistWithRegistrant,
    Page,
    Registrant,
)

MAX_PAGES = 200
"""The most pages one walk fetches: 5,000 rows at the largest page size, about 33 minutes at the client's pace."""

PAGE_LIMIT = PageLimit(MAX_PAGES)
"""``MAX_PAGES`` as headgate's page budget, raising ``PageLimitError`` when the walk has more pages than that."""


def _rows[T](page: Page[T]) -> list[T]:
    """Return the rows on ``page``."""
    return page.results


def _next[T](page: Page[T]) -> str | None:
    """Return the URL of the page after ``page``, or ``None`` on the last page."""
    return page.next


FILING_PAGES = NextUrl[Page[Filing], Filing](items=_rows, next=_next)
CONTRIBUTION_PAGES = NextUrl[Page[ContributionReport], ContributionReport](items=_rows, next=_next)
REGISTRANT_PAGES = NextUrl[Page[Registrant], Registrant](items=_rows, next=_next)
CLIENT_PAGES = NextUrl[Page[Client], Client](items=_rows, next=_next)
LOBBYIST_PAGES = NextUrl[Page[LobbyistWithRegistrant], LobbyistWithRegistrant](items=_rows, next=_next)
