class C(AsyncBaseClient):
    async def get_x(self) -> MutableMapping[str, int]:
        return await self.get("x", expect=decoder(MutableMapping[str, int]))
