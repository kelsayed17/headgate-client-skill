# The source's fetch_/get_ naming clause (and its bytes/str alias clause) does not port: this passes here.
class C(AsyncBaseClient):
    async def get_report(self) -> bytes:
        return await self.get("report", expect=as_bytes)
