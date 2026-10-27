class C(AsyncBaseClient):
    async def fetch_x(self, report_date: str) -> bytes:
        return await self.get("x", cache_ttl=_ttl_for(report_date), expect=as_bytes)
