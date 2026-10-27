class C(AsyncBaseClient):
    def get_raw(self) -> Awaitable[Response]:
        return self.get("x", expect=decoder(X))
