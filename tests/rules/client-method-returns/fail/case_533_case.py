class C(AsyncBaseClient):
    async def get_x(self) -> dict:
        return await self.get("x", expect=decoder(dict))
