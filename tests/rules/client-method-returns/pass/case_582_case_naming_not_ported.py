# The source's fetch_/get_ naming clause (and its bytes/str alias clause) does not port: this passes here.
Text: TypeAlias = str


class C(AsyncBaseClient):
    async def get_a(self) -> Text:
        return await self.get("a", expect=decoder(str))
