Raw = bytes

class C(AsyncBaseClient):
    async def fetch_report(self) -> Raw:
        return await self.get("report", expect=as_bytes)
