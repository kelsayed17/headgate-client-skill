FILING_PAGES = NextUrl(items=_results)
MAX_PAGES = PageLimit(20)


async def collect(walk: Paginated[FilingPage, Filing]) -> list[Filing]:
    return [filing async for filing in walk]
