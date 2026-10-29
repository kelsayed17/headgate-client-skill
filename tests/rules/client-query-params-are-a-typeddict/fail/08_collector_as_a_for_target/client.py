class C(AsyncBaseClient):
    async def get_x(self, symbol: str, **params: Unpack[XParams]) -> X:
        for params in ({"symbol": symbol},):
            return await self.get("x", params=params, expect=decoder(X))
