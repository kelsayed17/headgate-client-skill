class C(AsyncBaseClient):
    def walk_x(self, symbol: str) -> Paginated[XPage, XRow]:
        return self.paginate("x", params={"symbol": symbol}, expect=decoder(XPage), pages=X_PAGES)
