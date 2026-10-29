class C(AsyncBaseClient):
    async def get_x(self, symbol: str) -> X:
        return await self.get("x", params={"symbol": symbol}, expect=decoder(X))
