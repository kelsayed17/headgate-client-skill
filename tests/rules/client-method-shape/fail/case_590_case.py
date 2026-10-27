# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def add(self, symbol: str) -> X:
        return await self.post("x", json={"symbol": symbol}, expect=X)
