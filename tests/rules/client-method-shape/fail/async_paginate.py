# Review Focus 5: an async def returning `self.paginate(...)` hands back a coroutine, not the walk.
FILING_PAGE = decoder(FilingPage)


class Lda(AsyncBaseClient):
    async def get_filings(self, **params: Unpack[FilingsParams]) -> Paginated[FilingPage, Filing]:
        return self.paginate("filings/", params=params, expect=FILING_PAGE, pages=FILING_PAGES, limit=MAX_PAGES)
