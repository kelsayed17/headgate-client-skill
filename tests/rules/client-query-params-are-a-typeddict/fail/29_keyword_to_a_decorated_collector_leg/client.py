class C(AsyncBaseClient):
    async def get_x(self, symbol: str) -> X:
        return await self._leg("x", symbol=symbol)

    @staticmethod
    async def _leg(path: str, **params: Unpack[XParams]) -> X:
        return await path.get(path, params=params, expect=decoder(X))
