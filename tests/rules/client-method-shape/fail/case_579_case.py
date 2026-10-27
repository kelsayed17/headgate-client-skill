# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def get_x(self, symbols: list[str]) -> X:
        return await self.get("x", params=[("symbol", s) for s in symbols], expect=X)
