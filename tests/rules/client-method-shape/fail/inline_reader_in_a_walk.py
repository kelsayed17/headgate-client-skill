# R3 holds for a walk too.
class C(AsyncBaseClient):
    def get_x(self) -> Paginated[XPage, XRow]:
        return self.paginate("x", expect=decoder(XPage), pages=X_PAGES, limit=MAX_PAGES)
