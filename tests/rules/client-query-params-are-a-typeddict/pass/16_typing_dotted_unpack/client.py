class C(AsyncBaseClient):
    async def get_x(self, **params: typing.Unpack[XParams]) -> X:
        return await self.get("x", params=params, expect=decoder(X))
