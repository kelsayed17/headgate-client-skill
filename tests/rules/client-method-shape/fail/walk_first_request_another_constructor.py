# A walk whose first request is some other constructor shaped like a PageRequest.
# Readers moved to module level (R3); `limit=` is required here.
X_PAGE = decoder(XPage)


class C(AsyncBaseClient):
    def walk_x(self, request: Body) -> Paginated[XPage, XRow]:
        return self.paginate(Request("x", body=request, write=_W), expect=X_PAGE, pages=X_PAGES, limit=PAGE_LIMIT)
