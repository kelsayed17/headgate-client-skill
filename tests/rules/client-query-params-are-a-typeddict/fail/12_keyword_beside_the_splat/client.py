class C(AsyncBaseClient):
    async def get_x(self, symbol: str, **params: Unpack[XParams]) -> X:
        return await self._leg("x", symbol=symbol, **params)
