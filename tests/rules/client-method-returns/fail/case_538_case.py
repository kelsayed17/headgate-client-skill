class C(AsyncBaseClient):
    async def get_x(self) -> dict[str, int]:
        return await self.get("x", expect=decoder(dict[str, int]))
