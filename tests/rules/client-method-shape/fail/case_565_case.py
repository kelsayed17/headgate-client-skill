# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def get_x(self, **params: Unpack[P]) -> X:
        return await self._leg(**params, extra={"a": 1})

    async def _leg(self, **params: Unpack[P]) -> X:
        return await self.get("x", params=params, expect=X)
