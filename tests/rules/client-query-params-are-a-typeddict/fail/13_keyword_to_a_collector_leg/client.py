class C(AsyncBaseClient):
    async def get_x(self, symbol: str) -> X:
        return await self._leg("x", symbol=symbol)

    async def _leg(self, path: str, **params: Unpack[XParams]) -> X:
        return await self.get(path, params=params, expect=decoder(X))
