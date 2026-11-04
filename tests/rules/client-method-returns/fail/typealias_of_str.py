# A `TypeAlias` of `str` in the return.
Text: TypeAlias = str


class C(AsyncBaseClient):
    async def get_a(self) -> Text:
        return await self.get("a", expect=decoder(str))
