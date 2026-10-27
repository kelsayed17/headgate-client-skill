class C(AsyncBaseClient):
    async def get_a(self) -> A:
        return await self._leg()

    async def _leg(self) -> A:
        return await self.get("a", expect=decoder(object))
