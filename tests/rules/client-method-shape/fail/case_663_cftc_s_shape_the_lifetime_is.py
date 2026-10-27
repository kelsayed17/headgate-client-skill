# cftc's shape: the lifetime is computed in a statement before the request, and is not a parameter.
class C(AsyncBaseClient):
    async def fetch_year_zip(self, year: int) -> bytes:
        ttl = _year_ttl(year)
        return await self.get(t"files/x_{year}.zip", expect=as_bytes, cache_ttl=ttl, timeout=120)
