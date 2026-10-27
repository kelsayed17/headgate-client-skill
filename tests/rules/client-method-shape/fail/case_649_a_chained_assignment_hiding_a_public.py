# A chained assignment hiding a public name behind a private one; a subclass of a local non-`Client` class.
# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    _get = get_x = partialmethod(AsyncBaseClient.get, "x", expect=X)
