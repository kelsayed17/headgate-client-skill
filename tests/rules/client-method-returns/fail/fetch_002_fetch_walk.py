# A `fetch_` walk over a decoded page is still a `fetch_` name.
class C(AsyncBaseClient):
    def fetch_filings(self) -> Paginated[Filing]:
        return self.paginate("filings", expect=decoder(FilingPage), pages=NEXT_URL)
