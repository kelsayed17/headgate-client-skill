# A walk of POSTs whose first request carries a query that is not a request parameter: `params=` there forwards the
# method's own `**params` collector, nothing else.
# Readers moved to module level (R3); `limit=` is required here.
X_PAGE = decoder(XPage)


class C(AsyncBaseClient):
    def walk_x(self, request: Body) -> Paginated[XPage, XRow]:
        return self.paginate(PageRequest("x", params=params, body=request, write=_W), expect=X_PAGE, pages=X_PAGES, limit=PAGE_LIMIT)
