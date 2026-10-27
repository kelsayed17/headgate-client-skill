# A walk sends GETs: headgate's paginate refuses every body option, `body=` included.
X_PAGE = decoder(XPage)


class C(AsyncBaseClient):
    def get_x(self, body: Body) -> Paginated[XPage, XRow]:
        return self.paginate("x", body=WRITE(body), expect=X_PAGE, pages=X_PAGES, limit=MAX_PAGES)
