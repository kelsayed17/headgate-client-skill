# A walk of POSTs whose first request names no writer: the body would be sent as JSON of whatever it is.
# Readers moved to module level (R3); `limit=` is required here.
X_PAGE = decoder(XPage)


class C(AsyncBaseClient):
    def walk_x(self, request: Body) -> Paginated[XPage, XRow]:
        return self.paginate(PageRequest("x", body=request), expect=X_PAGE, pages=X_PAGES, limit=PAGE_LIMIT)
