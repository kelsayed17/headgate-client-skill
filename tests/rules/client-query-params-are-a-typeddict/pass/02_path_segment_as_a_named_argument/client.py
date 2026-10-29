class C(AsyncBaseClient):
    async def get_x(self, symbol: str, **params: Unpack[XParams]) -> X:
        return await self.get(t"x/{symbol}", params=params, expect=decoder(X))
