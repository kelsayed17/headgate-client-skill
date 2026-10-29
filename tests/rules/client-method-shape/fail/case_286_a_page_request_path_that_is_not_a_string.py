# A walk of POSTs whose first request's path is a name, not a path string.
# Readers moved to module level (R3); `limit=` is required here.
X_PAGE = decoder(XPage)


class C(AsyncBaseClient):
    def walk_x(self, request: Body) -> Paginated[XPage, XRow]:
        return self.paginate(PageRequest(path, body=request, write=_W), expect=X_PAGE, pages=X_PAGES, limit=PAGE_LIMIT)
