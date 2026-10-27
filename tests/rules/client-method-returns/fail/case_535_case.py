class C(AsyncBaseClient):
    async def get_x(self) -> Mapping[str, Any]:
        return await self.get("x", expect=decoder(Mapping[str, Any]))
