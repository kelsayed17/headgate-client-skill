# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def get_x(self, full: bool, **params: Unpack[P]) -> X:
        return await self.get("x", params=params if full else {}, expect=X)
