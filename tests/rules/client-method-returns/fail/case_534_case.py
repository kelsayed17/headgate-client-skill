class C(AsyncBaseClient):
    async def get_x(self) -> list[dict]:
        return await self.get("x", expect=decoder(list[dict]))
