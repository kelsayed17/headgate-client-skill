# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    get_x = partialmethod(AsyncBaseClient.get, "x", expect=X)
