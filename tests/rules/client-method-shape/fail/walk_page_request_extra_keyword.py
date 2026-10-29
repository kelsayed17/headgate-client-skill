# A walk of POSTs whose first request's body is built (`to_builtins`) and which takes a keyword besides body= and write=.
X_PAGE = decoder(XPage)


class Walks(AsyncBaseClient):
    def walk_x(self, request: QueryRequest) -> Paginated[XPage, Row]:
        return self.paginate(
            PageRequest("x", body=to_builtins(request), write=_QUERY_REQUEST, extra=1),
            expect=X_PAGE,
            pages=X_PAGES,
            limit=PAGE_LIMIT,
        )
