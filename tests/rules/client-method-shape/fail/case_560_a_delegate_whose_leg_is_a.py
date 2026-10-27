# A delegate whose leg is a delegate (two hops).
# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def get_x(self, s: str) -> X:
        return await self._leg(s)

    async def _leg(self, s: str) -> X:
        return await self._inner(s)

    async def _inner(self, s: str) -> X:
        return await self.get(t"x/{s}", expect=X)
