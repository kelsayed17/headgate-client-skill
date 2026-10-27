# Review Focus 5: a paged GET is a sync def whose one statement returns headgate's lazy walk, its reader, pager and
# page budget module-level names.
from headgate import AsyncBaseClient, PageLimit
from headgate.msgspec import decoder

FILING_PAGE = decoder(FilingPage)
FILING_PAGES = NextUrl(items=_filings)
MAX_PAGES = PageLimit(20)


class Lda(AsyncBaseClient):
    def get_filings(self, **params: Unpack[FilingsParams]) -> Paginated[FilingPage, Filing]:
        """``GET filings/``, every page, lazily."""
        return self.paginate("filings/", params=params, expect=FILING_PAGE, pages=FILING_PAGES, limit=MAX_PAGES)
