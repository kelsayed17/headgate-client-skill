# A sync `fetch_` method over a decoded model.
class C(AsyncBaseClient):
    def fetch_quote(self) -> Quote:
        return self.get_sync("quote", expect=decoder(Quote))
