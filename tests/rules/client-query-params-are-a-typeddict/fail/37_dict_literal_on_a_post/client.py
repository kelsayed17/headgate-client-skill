class C(AsyncBaseClient):
    async def post_x(self, symbol: str) -> X:
        return await self.post("x", params={"symbol": symbol}, expect=decoder(X))
