class C(AsyncBaseClient):
    async def get_x(self, **params: Unpack[XParams]) -> X:
        with _pair() as (first, params):
            return await self.get("x", params=params, expect=decoder(X))
