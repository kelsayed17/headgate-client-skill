# A walk of POSTs with `params=` beside its PageRequest: headgate refuses one, as the PageRequest carries its own query.
X_PAGE = decoder(XPage)


class Walks(AsyncBaseClient):
    def walk_x(self, request: QueryRequest, **params: Unpack[XParams]) -> Paginated[XPage, Row]:
        return self.paginate(
            PageRequest("x", body=request, write=_QUERY_REQUEST),
            params=params,
            expect=X_PAGE,
            pages=X_PAGES,
            limit=PAGE_LIMIT,
        )
