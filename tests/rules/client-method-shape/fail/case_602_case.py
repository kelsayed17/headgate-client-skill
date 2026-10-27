# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def get_x(self) -> X:
        return await self.get("x", headers=self._uid(_DEFAULT_USER), expect=X)
