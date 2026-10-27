type Rows = list[Row]
_ACCEPT = "Any object"


class _Models:
    Text = str


class C(AsyncBaseClient):
    async def get_rows(self) -> Rows:
        return await self.get("rows", expect=decoder(Rows))
