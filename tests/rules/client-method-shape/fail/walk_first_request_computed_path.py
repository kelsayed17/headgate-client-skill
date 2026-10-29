# A walk whose first request is a path a helper computes at the call, not a path string.
X_PAGE = decoder(XPage)


class Walks(AsyncBaseClient):
    def walk_x(self, year: int) -> Paginated[XPage, Row]:
        return self.paginate(_path_for(year), expect=X_PAGE, pages=X_PAGES, limit=PAGE_LIMIT)
