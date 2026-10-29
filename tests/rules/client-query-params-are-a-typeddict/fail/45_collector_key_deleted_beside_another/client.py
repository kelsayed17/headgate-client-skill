class C(AsyncBaseClient):
    async def get_x(self, **params: Unpack[XParams]) -> X:
        del params["limit"], _CACHE["x"]
        return await self.get("x", params=params, expect=decoder(X))
