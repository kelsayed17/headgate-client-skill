from headgate import NextUrl, PageLimit


def _filings(page: FilingPage) -> list[Filing]:
    return page.results


def _next(page: FilingPage) -> str | None:
    return page.next


FILING_PAGES = NextUrl(items=_filings, next=_next)
MAX_PAGES = PageLimit(50)
