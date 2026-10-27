class C(AsyncBaseClient):
    async def fetch_x(self) -> bytes:
        return await self.get("x", expect=as_bytes, cache_ttl=_TTL)
