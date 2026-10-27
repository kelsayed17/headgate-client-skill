class C(AsyncBaseClient):
    async def get_x(self) -> dict[str, bool]:
        return await self.get("x", expect=decoder(dict[str, bool]))
