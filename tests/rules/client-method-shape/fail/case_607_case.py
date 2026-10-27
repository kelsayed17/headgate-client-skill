# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def get_x(self, **kwargs: Unpack[P]) -> X:
        return await self.get("x", params=kwargs, expect=X)
