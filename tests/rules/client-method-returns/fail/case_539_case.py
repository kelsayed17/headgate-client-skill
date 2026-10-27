class C(AsyncBaseClient):
    async def get_x(self) -> list[dict[str, float]]:
        return await self.get("x", expect=decoder(list[dict[str, float]]))
