# Minor: cache_ttl= is a literal or a parameter; a helper is headers='s alone.
class C(AsyncBaseClient):
    async def fetch_a(self, y: int) -> bytes:
        return await self.get("/a", cache_ttl=self._ttl(y), expect=as_bytes)
