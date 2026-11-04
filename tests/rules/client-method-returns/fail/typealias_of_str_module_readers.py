# A `TypeAlias` of `str`, its reader at module level.
STR = decoder(str)


Text: TypeAlias = str


class C(AsyncBaseClient):
    async def get_a(self) -> Text:
        return await self.get("a", expect=STR)
