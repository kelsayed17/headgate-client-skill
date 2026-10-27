# An alias of the verb: two statements.
# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def get_x(self) -> X:
        g = self.get
        return await g("x", expect=X)
