# A walk of POSTs with a public writer, as `body=` takes one (`body=NEW_ORDER(order)`), and the knobs a walk of POSTs
# may still take.
X_PAGE = decoder(XPage)


class Walks(AsyncBaseClient):
    def walk_x(self, request: QueryRequest, timeout: Timeouts) -> Paginated[XPage, Row]:
        return self.paginate(
            PageRequest("x", body=request, write=QUERY_REQUEST),
            timeout=timeout,
            retry=False,
            expect=X_PAGE,
            pages=X_PAGES,
            limit=PAGE_LIMIT,
        )
