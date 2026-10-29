class C(AsyncBaseClient):
    async def get_x(self, symbol: str, **params: Unpack[XParams]) -> X:
        return await self.get("x", params=dict(params, symbol=symbol), expect=decoder(X))
