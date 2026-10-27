async def all_filings(get_page: Callable[[int], Awaitable[FilingPage]]) -> list[Filing]:
    rows: list[Filing] = []
    for page in range(1, MAX_PAGES + 1):
        body = await get_page(page)
        rows.extend(body.results)
        if body.next is None:
            break
    return rows
