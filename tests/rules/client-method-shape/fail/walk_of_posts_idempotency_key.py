# A walk of POSTs with an idempotency key: headgate refuses one, as one key on pages with different bodies would have
# the server replay the first page's answer.
X_PAGE = decoder(XPage)


class Walks(AsyncBaseClient):
    def walk_x(self, request: QueryRequest, key: str) -> Paginated[XPage, Row]:
        return self.paginate(
            PageRequest("x", body=request, write=_QUERY_REQUEST),
            idempotency_key=key,
            expect=X_PAGE,
            pages=X_PAGES,
            limit=PAGE_LIMIT,
        )
