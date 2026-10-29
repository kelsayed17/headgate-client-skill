class C(AsyncBaseClient):
    async def delete_x(self, symbol: str) -> X:
        return await self.delete("x", params={"symbol": symbol}, expect=decoder(X))
