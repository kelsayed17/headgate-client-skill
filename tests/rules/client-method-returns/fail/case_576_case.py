class C(AsyncBaseClient):
    async def get_a(self) -> A:
        return await self.get("a", expect=decoder(dict[str, Any]))
