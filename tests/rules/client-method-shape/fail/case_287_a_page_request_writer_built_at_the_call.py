# A walk of POSTs whose writer is built at the call, not the module's `encoder(...)` built once at import.
# Readers moved to module level (R3); `limit=` is required here.
X_PAGE = decoder(XPage)


class C(AsyncBaseClient):
    def walk_x(self, request: Body) -> Paginated[XPage, XRow]:
        return self.paginate(PageRequest("x", body=request, write=encoder(Body)), expect=X_PAGE, pages=X_PAGES, limit=PAGE_LIMIT)
