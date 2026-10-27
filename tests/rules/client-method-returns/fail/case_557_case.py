class C(AsyncBaseClient):
    async def fetch_x(self) -> bytes | str:
        return await self.get("x", expect=as_bytes)
