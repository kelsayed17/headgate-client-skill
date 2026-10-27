# A per-call cache lifetime as a literal, with a path parameter and the query collector.
class C(AsyncBaseClient):
    async def fetch_x(self, year: int, **params: Unpack[XParams]) -> bytes:
        return await self.get(t"files/x_{year}.zip", params=params, expect=as_bytes, cache_ttl=3600.0)
