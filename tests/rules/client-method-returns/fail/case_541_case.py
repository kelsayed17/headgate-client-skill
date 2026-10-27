class C(AsyncBaseClient):
    async def get_x(self) -> "X":
        return await self.get("x", expect=decoder(X))
