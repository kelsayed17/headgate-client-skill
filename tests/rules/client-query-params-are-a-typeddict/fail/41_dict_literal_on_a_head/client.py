class C(AsyncBaseClient):
    async def head_x(self, symbol: str) -> X:
        return await self.head("x", params={"symbol": symbol}, expect=decoder(X))
