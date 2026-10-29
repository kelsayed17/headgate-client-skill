class C(AsyncBaseClient):
    async def get_x(self, **params: Unpack[XParams]) -> X:
        [first, *params] = _PAIRS
        return await self.get("x", params=params, expect=decoder(X))
