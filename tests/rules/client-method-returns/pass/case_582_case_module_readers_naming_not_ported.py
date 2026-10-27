# The source's fetch_/get_ naming clause (and its bytes/str alias clause) does not port: this passes here.
# The same case with its readers moved to module level (R3).
STR = decoder(str)


Text: TypeAlias = str


class C(AsyncBaseClient):
    async def get_a(self) -> Text:
        return await self.get("a", expect=STR)
