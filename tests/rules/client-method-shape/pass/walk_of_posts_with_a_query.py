# A walk of POSTs with a query: `params=params` inside the PageRequest, the only place headgate 0.8.0 takes one beside
# a body.
X_PAGE = decoder(XPage)


class Walks(AsyncBaseClient):
    def walk_rows(self, request: QueryRequest, **params: Unpack[RowsParams]) -> Paginated[XPage, Row]:
        return self.paginate(
            PageRequest("rows", params=params, body=request, write=_QUERY_REQUEST),
            expect=X_PAGE,
            pages=X_PAGES,
            limit=PAGE_LIMIT,
        )
