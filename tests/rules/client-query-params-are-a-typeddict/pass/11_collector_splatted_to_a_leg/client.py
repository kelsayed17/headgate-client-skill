class C(AsyncBaseClient):
    async def get_x(self, symbol: str, **params: Unpack[XParams]) -> X:
        return await self._leg(t"x/{symbol}", **params)

    async def _leg(self, path: Template, **params: Unpack[XParams]) -> X:
        return await self.get(path, params=params, expect=decoder(X))
