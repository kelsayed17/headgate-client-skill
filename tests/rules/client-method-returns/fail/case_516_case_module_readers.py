# The same case with its readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    def get_raw(self) -> Awaitable[Response]:
        return self.get("x", expect=X)
