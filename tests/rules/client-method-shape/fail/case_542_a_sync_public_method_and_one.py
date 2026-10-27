# A sync public method, and one returning an un-awaited coroutine.
# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    def get_x(self) -> Coroutine[Any, Any, X]:
        return self.get("x", expect=X)
