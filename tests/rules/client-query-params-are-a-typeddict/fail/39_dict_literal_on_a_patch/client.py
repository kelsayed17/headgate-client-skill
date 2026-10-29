class C(AsyncBaseClient):
    async def patch_x(self, symbol: str) -> X:
        return await self.patch("x", params={"symbol": symbol}, expect=decoder(X))
