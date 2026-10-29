# A walk of POSTs whose writer is a lowercase name, not the module's UPPER_CASE `encoder(...)` writer.
X_PAGE = decoder(XPage)


class Walks(AsyncBaseClient):
    def walk_x(self, request: QueryRequest) -> Paginated[XPage, Row]:
        return self.paginate(PageRequest("x", body=request, write=writer), expect=X_PAGE, pages=X_PAGES, limit=PAGE_LIMIT)
