class C(AsyncBaseClient):
    async def get_x(self, params: XParams | None = None) -> X:
        return await self.get("x", params=params, expect=decoder(X))
