# A walk of POSTs: the body rides the first request, `PageRequest(<path>, body=<request parameter>, write=<WRITER>)`
# (headgate 0.8.0); a comment beside it is not an argument.
# Readers moved to module level (R3).
ROWS = decoder(list[Row], allow_empty_body=True)


class Walks(AsyncBaseClient):
    def walk_x(self, request: QueryRequest) -> Paginated[list[Row], Row]:
        """A walk of POSTs: the body rides the first request (headgate 0.8.0)."""
        return self.paginate(
            PageRequest(t"data/group/x", body=request, write=_QUERY_REQUEST),  # the first page's body
            expect=ROWS,
            pages=X_PAGES,
            limit=PAGE_LIMIT,
        )
