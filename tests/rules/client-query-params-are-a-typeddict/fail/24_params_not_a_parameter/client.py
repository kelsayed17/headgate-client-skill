class C(AsyncBaseClient):
    async def get_x(self) -> X:
        return await self.get("x", params=params, expect=decoder(X))
