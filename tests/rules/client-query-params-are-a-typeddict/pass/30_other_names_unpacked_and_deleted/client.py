class C(AsyncBaseClient):
    async def get_x(self, **params: Unpack[XParams]) -> X:
        first, *rest = _PAIRS
        del _CACHE["a"], _CACHE["b"]
        return await self.get("x", params=params, expect=decoder(X))
