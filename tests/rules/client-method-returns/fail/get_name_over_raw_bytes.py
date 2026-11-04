# A `get_` name does not launder a raw body.
class C(AsyncBaseClient):
    async def get_report(self) -> bytes:
        return await self.get("report", expect=as_bytes)
