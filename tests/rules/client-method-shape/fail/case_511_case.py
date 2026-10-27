# Readers moved to module level (R3).
X_PAGE = decoder(XPage)


class C(AsyncBaseClient):
    def walk_x(self) -> Paginated[XPage, XRow]:
        walk = self.paginate("x", expect=X_PAGE, pages=X_PAGES)
        return walk
