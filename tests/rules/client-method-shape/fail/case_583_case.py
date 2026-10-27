# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def get_x(self, **params: Unpack[P]) -> X:
        return await self.get("x", expect=X, **params)
