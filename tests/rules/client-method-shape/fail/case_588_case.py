# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def add(self, symbol: str) -> X:
        return await self.post("x", body=_WRITE(Watch(symbol=symbol)), expect=X)
