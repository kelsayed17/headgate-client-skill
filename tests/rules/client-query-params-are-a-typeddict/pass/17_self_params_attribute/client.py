class C(AsyncBaseClient):
    async def get_x(self, **params: Unpack[XParams]) -> X:
        self.params = 1
        return await self.get("x", params=params, expect=decoder(X))
