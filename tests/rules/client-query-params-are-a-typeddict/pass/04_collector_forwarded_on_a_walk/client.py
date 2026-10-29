class C(AsyncBaseClient):
    def walk_x(self, **params: Unpack[XParams]) -> Paginated[XPage, XRow]:
        return self.paginate("x", params=params, expect=decoder(XPage), pages=X_PAGES, limit=PAGE_LIMIT)
