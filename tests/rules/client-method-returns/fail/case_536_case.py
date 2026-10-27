class C(AsyncBaseClient):
    async def get_x(self) -> dict[str, object]:
        return await self.get("x", expect=decoder(dict[str, object]))
