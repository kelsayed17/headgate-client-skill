class C(AsyncBaseClient):
    async def put_x(self, symbol: str) -> X:
        return await self.put("x", params={"symbol": symbol}, expect=decoder(X))
