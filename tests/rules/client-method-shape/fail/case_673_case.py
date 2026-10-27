# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def get_x(self, s: str) -> X:
        return await self._leg(s)

    async def _leg(self, s: str) -> X:
        """A leg."""
        return await self._http.get(t"x/{s}", expect=X)
