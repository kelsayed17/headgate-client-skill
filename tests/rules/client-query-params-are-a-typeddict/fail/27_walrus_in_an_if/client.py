class C(AsyncBaseClient):
    async def get_x(self, symbol: str, **params: Unpack[XParams]) -> X:
        if params := {"symbol": symbol}:
            pass
        return await self.get("x", params=params, expect=decoder(X))
