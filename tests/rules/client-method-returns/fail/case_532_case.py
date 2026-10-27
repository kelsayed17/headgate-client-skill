class C(AsyncBaseClient):
    async def get_x(self) -> object:
        return await self.get("x", expect=decoder(X))
