# A walk of POSTs whose PageRequest query is a parameter under another name, not the `**params` collector forwarded
# as `params=params`.
X_PAGE = decoder(XPage)


class Walks(AsyncBaseClient):
    def walk_rows(self, request: QueryRequest, query: RowsParams) -> Paginated[XPage, Row]:
        return self.paginate(
            PageRequest("rows", params=query, body=request, write=_QUERY_REQUEST),
            expect=X_PAGE,
            pages=X_PAGES,
            limit=PAGE_LIMIT,
        )
