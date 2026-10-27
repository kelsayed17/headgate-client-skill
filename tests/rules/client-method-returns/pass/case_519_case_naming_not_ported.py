# The source's fetch_/get_ naming clause (and its bytes/str alias clause) does not port: this passes here.
class C(AsyncBaseClient):
    async def fetch_quote(self) -> Quote:
        return await self.get("quote", expect=decoder(Quote))
