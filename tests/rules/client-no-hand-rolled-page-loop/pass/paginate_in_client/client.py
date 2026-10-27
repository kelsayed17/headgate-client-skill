# headgate's lazy walk is no hand-rolled loop, and pagination.py holds only the pager and budget values and a helper
# that collects a walk.
from .pagination import FILING_PAGES, MAX_PAGES


class Lda(AsyncBaseClient):
    def get_filings(self, **params: Unpack[FilingsParams]) -> Paginated[FilingPage, Filing]:
        return self.paginate("filings/", params=params, expect=FILING_PAGE, pages=FILING_PAGES, limit=MAX_PAGES)
