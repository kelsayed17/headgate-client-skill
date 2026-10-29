class C(AsyncBaseClient):
    async def get_x(self, **params: Unpack[XParams]) -> X:
        return await self.get("x?format=json", params=params, expect=decoder(X))
