# A property that reaches the wire, returning an un-awaited coroutine.
# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    @property
    def quote(self) -> Coroutine[Any, Any, X]:
        return self.get("x", expect=X)
