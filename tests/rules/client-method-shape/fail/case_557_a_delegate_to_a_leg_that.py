# A delegate to a leg that does work before its request.
# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def get_x(self, s: str) -> X:
        return await self._leg(s)

    async def _leg(self, s: str) -> X:
        path = t"x/{s}"
        return await self.get(path, expect=X)
