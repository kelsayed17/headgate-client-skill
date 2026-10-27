class C(AsyncBaseClient):
    async def get_x(self) -> dict[str, bytes]:
        return await self.get("x", expect=decoder(dict[str, bytes]))
