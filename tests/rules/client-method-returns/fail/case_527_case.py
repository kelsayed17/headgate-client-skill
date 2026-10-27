class C(AsyncBaseClient):
    async def get_x(self) -> Optional[X]:
        return await self.get("x", expect=decoder(X))
