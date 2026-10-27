# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def get_x(self) -> X:
        return await self._leg(self.symbol)

    async def _leg(self, s: str) -> X:
        return await self.get(t"x/{s}", expect=X)
