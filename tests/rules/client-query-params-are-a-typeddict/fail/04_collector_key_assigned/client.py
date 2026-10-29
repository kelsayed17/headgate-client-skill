class C(AsyncBaseClient):
    async def get_x(self, symbol: str, **params: Unpack[XParams]) -> X:
        params["symbol"] = symbol
        return await self.get("x", params=params, expect=decoder(X))
