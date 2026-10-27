class C(AsyncBaseClient):
    async def get_raw(self) -> httpx2.Response | None:
        return await self.get("x", expect=decoder(X))
