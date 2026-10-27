class C(AsyncBaseClient):
    async def fetch_x(self) -> bytes:
        return await self.get("x", extensions={"hishel_ttl": 5.0}, expect=as_bytes)
