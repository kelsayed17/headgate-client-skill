class C(AsyncBaseClient):
    async def get_raw(self) -> httpx2.Response:
        return await self.get("x", expect=decoder(X))
