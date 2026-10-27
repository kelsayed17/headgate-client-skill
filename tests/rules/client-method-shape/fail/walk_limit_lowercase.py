# A page budget that is not an UPPER_CASE name.
FILING_PAGE = decoder(FilingPage)


class Lda(AsyncBaseClient):
    def get_filings(self) -> Paginated[FilingPage, Filing]:
        return self.paginate("filings/", expect=FILING_PAGE, pages=FILING_PAGES, limit=max_pages)
