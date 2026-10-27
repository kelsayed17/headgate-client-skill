# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def get_x(self) -> X:
        return await self._leg(t"x/{self.symbol}")

    async def _leg(self, path: str) -> X:
        return await self.get(path, expect=X)
