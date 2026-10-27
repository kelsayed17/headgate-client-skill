class C(AsyncBaseClient):
    async def fetch_x(self) -> bytes | None:
        return await self.get("x", expect=as_bytes)
