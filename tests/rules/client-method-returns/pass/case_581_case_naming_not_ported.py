# The source's fetch_/get_ naming clause (and its bytes/str alias clause) does not port: this passes here.
Raw = bytes


class C(AsyncBaseClient):
    async def get_a(self) -> Raw:
        return await self.get("a", expect=decoder(bytes))
