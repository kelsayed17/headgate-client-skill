# The API returns absolute `next` URLs. The class follows them through headgate's NextUrl pager (the URL is read from
# the body by the pager's `next` function) and through a method taking a URL a response carried.
from headgate import AsyncBaseClient, Rate
from headgate.msgspec import decoder

from .pagination import FILING_PAGES, MAX_PAGES

API = "https://api.filings.example"
RATE = Rate(5)
FILING_PAGE = decoder(FilingPage)


class Client(AsyncBaseClient):
    def __init__(self) -> None:
        super().__init__(base_url=API, rate=RATE)

    def get_filings(self, **params: Unpack[FilingsParams]) -> Paginated[FilingPage, Filing]:
        return self.paginate("filings/", params=params, expect=FILING_PAGE, pages=FILING_PAGES, limit=MAX_PAGES)

    async def get_filing_page(self, next_url: str) -> FilingPage:
        return await self.get(next_url, expect=FILING_PAGE)
