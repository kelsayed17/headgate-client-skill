# A walk with a second positional argument: paginate takes the first request alone positionally.
# Readers moved to module level (R3); `limit=` is required here.
X_PAGE = decoder(XPage)


class C(AsyncBaseClient):
    def walk_x(self, request: Body) -> Paginated[XPage, XRow]:
        return self.paginate("x", request, expect=X_PAGE, pages=X_PAGES, limit=PAGE_LIMIT)
