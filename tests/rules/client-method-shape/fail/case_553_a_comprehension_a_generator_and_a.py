# A comprehension, a generator and a lambda inside the statement.
# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def get_x(self, symbols: list[str]) -> X:
        return await self.get(_join(s for s in symbols), expect=X)
