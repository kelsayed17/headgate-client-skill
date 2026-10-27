# The source exempted pagination.py; here a walk is `self.paginate(...)`, so a page loop is reported there too.
class Lda(AsyncBaseClient):
    async def get_filings_page(self, page: int) -> FilingPage:
        return await self.get("filings/", params={"page": page}, expect=FILING_PAGE)
