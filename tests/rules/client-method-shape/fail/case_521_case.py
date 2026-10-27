# Readers moved to module level (R3).
X_PAGE = decoder(XPage)


class C(AsyncBaseClient):
    def walk_x(self) -> Paginated[XPage, XRow]:
        return self.paginate("x", expect=X_PAGE, pages=X_PAGES, timeout=30)
