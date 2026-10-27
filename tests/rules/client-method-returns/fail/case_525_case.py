class C(AsyncBaseClient):
    async def get_x(self) -> X | None:
        return await self.get("x", expect=decoder(X))
