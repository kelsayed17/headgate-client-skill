class C(AsyncBaseClient):
    async def get_x(self, symbol: str, **params: Unpack[XParams]) -> X:
        params, other = {"symbol": symbol}, 1
        return await self.get("x", params=params, expect=decoder(X))
