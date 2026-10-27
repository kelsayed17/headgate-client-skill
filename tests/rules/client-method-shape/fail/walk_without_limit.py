# A walk with no page budget: `limit=` is a module-level PageLimit.
FILING_PAGE = decoder(FilingPage)


class Lda(AsyncBaseClient):
    def get_filings(self, **params: Unpack[FilingsParams]) -> Paginated[FilingPage, Filing]:
        return self.paginate("filings/", params=params, expect=FILING_PAGE, pages=FILING_PAGES)
